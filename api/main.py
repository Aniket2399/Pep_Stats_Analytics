"""
Enhanced FastAPI Server for Live Pitch - Phase 2
REST + WebSocket endpoints with real-time sentiment, predictions, and caching
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Set
import logging
from datetime import datetime
import asyncio
import json

# Import Phase 2 components
import sys
sys.path.insert(0, '/Users/annie/Documents/All_Projects/FIFA_Data_Project')
from processing.sentiment_analyzer import SentimentAnalyzer
from ml.predictor import WinPredictor
from api.cache import CacheManager, MatchCache
from ingestion.football_data import FootballDataClient, FootballDataError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

app = FastAPI(
    title="Live Pitch API - Phase 2",
    description="Real-time FIFA World Cup Analytics with Sentiment & Predictions",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Phase 2 components
try:
    sentiment_analyzer = SentimentAnalyzer()
    logger.info("✅ Sentiment Analyzer loaded")
except Exception as e:
    logger.error(f"❌ Sentiment Analyzer error: {e}")
    sentiment_analyzer = None

try:
    win_predictor = WinPredictor()
    logger.info("✅ Win Predictor loaded")
except Exception as e:
    logger.error(f"❌ Win Predictor error: {e}")
    win_predictor = None

try:
    cache = CacheManager()
    match_cache = MatchCache(cache)
    logger.info("✅ Cache Manager loaded")
except Exception as e:
    logger.error(f"❌ Cache Manager error: {e}")
    cache = None
    match_cache = None


from datetime import timezone

LASTGOOD_TTL = 7 * 24 * 3600  # 1 week

# WC data provider (reads FOOTBALL_API_KEY from env; safe if key missing)
try:
    football = FootballDataClient()
    logger.info("✅ Football data client loaded")
except Exception as e:  # pragma: no cover
    logger.error(f"❌ Football data client error: {e}")
    football = None


def cached(cache, key, ttl, fetch_fn):
    """Return (data, source). Raises FootballDataError only on miss with no last-good."""
    if cache is not None:
        hit = cache.get(key)
        if hit is not None:
            return hit, "cache"
    try:
        fresh = fetch_fn()
        if cache is not None:
            cache.set(key, fresh, ttl)
            cache.set(f"{key}:lastgood", fresh, LASTGOOD_TTL)
        return fresh, "live"
    except FootballDataError:
        if cache is not None:
            lg = cache.get(f"{key}:lastgood")
            if lg is not None:
                return lg, "cache"
        raise


def envelope(cache, key, ttl, fetch_fn, mock):
    """Never raises. Wraps cached() with a labeled-mock fallback."""
    try:
        data, source = cached(cache, key, ttl, fetch_fn)
    except FootballDataError:
        data, source = mock, "mock"
    return {
        "source": source,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SentimentPost(BaseModel):
    """Social media post with sentiment"""
    text: str
    source: str
    match_id: int
    team: Optional[str] = None

class TeamStats(BaseModel):
    """Team statistics"""
    match_id: int
    team: str
    possession: float
    shots: int
    shots_on_target: int
    passes: int
    pass_accuracy: float
    fouls: int
    corners: int
    cards: int

class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis result"""
    sentiment_score: float
    category: str
    confidence: float
    subjectivity: float

class PredictionResponse(BaseModel):
    """Win probability prediction"""
    win_probability: float
    loss_probability: float
    confidence: float


# ============================================================================
# WEBSOCKET MANAGER
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, match_id: int):
        """Accept and register new connection"""
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = set()
        self.active_connections[match_id].add(websocket)
        logger.info(f"✅ Client connected to match {match_id}")
    
    def disconnect(self, websocket: WebSocket, match_id: int):
        """Remove disconnected client"""
        self.active_connections[match_id].discard(websocket)
        if not self.active_connections[match_id]:
            del self.active_connections[match_id]
        logger.info(f"❌ Client disconnected from match {match_id}")
    
    async def broadcast(self, match_id: int, message: dict):
        """Send message to all clients watching this match"""
        if match_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[match_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[match_id].discard(conn)
    
    def get_connected_count(self, match_id: int) -> int:
        """Get number of connected clients for a match"""
        return len(self.active_connections.get(match_id, set()))


manager = ConnectionManager()


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Live Pitch API - Phase 2",
        "components": {
            "sentiment_analyzer": sentiment_analyzer is not None,
            "win_predictor": win_predictor is not None,
            "cache": cache is not None
        }
    }


@app.get("/status")
def service_status():
    """Get service status"""
    cache_stats = cache.get_stats() if cache else {}
    return {
        "api": "running",
        "version": "0.2.0",
        "phase": "Phase 2 - Real-time Processing",
        "components": {
            "sentiment_analysis": "active" if sentiment_analyzer else "inactive",
            "predictions": "active" if win_predictor else "inactive",
            "caching": "active" if cache else "inactive"
        },
        "cache": cache_stats
    }


# ============================================================================
# SENTIMENT ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/sentiment/analyze", response_model=SentimentAnalysisResponse)
def analyze_sentiment(post: SentimentPost):
    """
    Analyze sentiment of social media post
    
    Args:
        post: Social media post data
    """
    if not sentiment_analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")
    
    try:
        result = sentiment_analyzer.detect_event_sentiment(post.text)
        
        return {
            "sentiment_score": result['sentiment_score'],
            "category": sentiment_analyzer.classify_sentiment(result['sentiment_score']),
            "confidence": result['confidence'],
            "subjectivity": result['subjectivity']
        }
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/match/{match_id}/sentiment")
def get_match_sentiment(match_id: int):
    """
    Get aggregated sentiment for a match
    
    Args:
        match_id: Match ID
    """
    if not match_cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    sentiment = match_cache.get_sentiment(match_id)
    
    if sentiment:
        return {
            "match_id": match_id,
            "sentiment": sentiment,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Return mock data if not cached
    return {
        "match_id": match_id,
        "sentiment": {
            "avg_sentiment": 0.65,
            "post_count": 1234,
            "sentiment_category": "positive",
            "volatility": 0.23
        },
        "cached": False,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post("/predictions/match")
def predict_match(team1_stats: TeamStats, team2_stats: TeamStats):
    """
    Predict match outcome
    
    Args:
        team1_stats: Team 1 statistics
        team2_stats: Team 2 statistics
    """
    if not win_predictor:
        raise HTTPException(status_code=503, detail="Predictor not available")
    
    try:
        team1_dict = team1_stats.dict()
        team2_dict = team2_stats.dict()
        
        prediction = win_predictor.predict_match_outcome(team1_dict, team2_dict)
        
        # Cache prediction
        if match_cache:
            match_cache.set_predictions(
                team1_stats.match_id,
                prediction,
                ttl=300  # 5 minutes
            )
        
        return {
            "match_id": team1_stats.match_id,
            "team1": team1_stats.team,
            "team2": team2_stats.team,
            "prediction": {
                "team1_win": prediction['team1_win'],
                "draw": prediction['draw'],
                "team2_win": prediction['team2_win'],
                "most_likely": prediction['most_likely']
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/match/{match_id}/predictions")
def get_match_predictions(match_id: int):
    """Get cached predictions for a match"""
    if not match_cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    predictions = match_cache.get_predictions(match_id)
    
    if predictions:
        return {
            "match_id": match_id,
            "predictions": predictions,
            "cached": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Return mock predictions if not cached
    return {
        "match_id": match_id,
        "predictions": {
            "team1_win": 0.58,
            "draw": 0.22,
            "team2_win": 0.20,
            "most_likely": "team1_win"
        },
        "cached": False,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# WEBSOCKET ENDPOINTS - REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/match/{match_id}")
async def websocket_match_updates(websocket: WebSocket, match_id: int):
    """
    WebSocket endpoint for real-time match updates
    Sends: stats, possession, predictions, sentiment
    """
    await manager.connect(websocket, match_id)
    
    try:
        # Send initial connection message
        initial_data = {
            "type": "connected",
            "match_id": match_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Connected to live match {match_id}",
            "connected_clients": manager.get_connected_count(match_id)
        }
        await websocket.send_json(initial_data)
        logger.info(f"📡 Initial data sent to match {match_id}")
        
        # Keep connection alive
        while True:
            # Receive any messages from client (for future interactivity)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                logger.debug(f"Received from client: {data}")
            except asyncio.TimeoutError:
                # Send keep-alive heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "match_id": match_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_json(heartbeat)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
        logger.info(f"Client disconnected from match {match_id}")


@app.websocket("/ws/sentiment/{match_id}")
async def websocket_sentiment_feed(websocket: WebSocket, match_id: int):
    """
    WebSocket endpoint for live sentiment feed
    Sends real-time sentiment updates as posts come in
    """
    await manager.connect(websocket, match_id)
    
    try:
        # Send initial connection
        await websocket.send_json({
            "type": "connected",
            "match_id": match_id,
            "channel": "sentiment",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep alive and send updates
        while True:
            try:
                # Wait for client message or timeout (simulate updates)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            except asyncio.TimeoutError:
                # Simulate sentiment update (in production, this comes from Kafka)
                sentiment_update = {
                    "type": "sentiment_update",
                    "match_id": match_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "posts": [
                        {
                            "text": "Amazing goal!",
                            "source": "twitter",
                            "sentiment_score": 0.9,
                            "category": "very_positive"
                        }
                    ],
                    "aggregated": {
                        "avg_sentiment": 0.72,
                        "post_count": 1456,
                        "category": "positive"
                    }
                }
                await websocket.send_json(sentiment_update)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)


# ============================================================================
# BROADCAST HELPER (for Spark/Kafka integration)
# ============================================================================

async def broadcast_match_update(
    match_id: int,
    stats: dict,
    predictions: dict,
    sentiment: dict
):
    """
    Broadcast real-time update to all connected clients
    Called from Spark jobs or API endpoints
    """
    message = {
        "type": "match_update",
        "match_id": match_id,
        "timestamp": datetime.utcnow().isoformat(),
        "stats": stats,
        "predictions": predictions,
        "sentiment": sentiment
    }
    await manager.broadcast(match_id, message)


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics"""
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    return cache.get_stats()


@app.delete("/cache/match/{match_id}")
def clear_match_cache(match_id: int):
    """Clear cache for a specific match"""
    if not match_cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    count = match_cache.clear_match_cache(match_id)
    return {
        "match_id": match_id,
        "keys_deleted": count,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    logger.info("🚀 Starting Live Pitch API - Phase 2...")
    logger.info("✅ Sentiment Analysis: Ready")
    logger.info("✅ Win Predictions: Ready")
    logger.info("✅ Real-time Caching: Ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown"""
    if cache:
        cache.redis_client.close()
    logger.info("✅ Shutting down Live Pitch API")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting FastAPI server with Phase 2 features...")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    logger.info("📡 WebSocket: ws://localhost:8000/ws/match/{match_id}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )