"""
Centralized Redis connection and operations manager.
Provides a single point of access for all Redis operations.
"""

from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Centralized Redis operations manager.
    """
    
    # Redis connection pool name
    DEFAULT_CONNECTION = "default"
    
    @staticmethod
    def get_connection(alias=DEFAULT_CONNECTION):
        """
        Get Redis connection from connection pool.
        
        Args:
            alias: Connection pool name (default: "default")
            
        Returns:
            Redis connection object
        """
        try:
            return get_redis_connection(alias)
        except Exception as e:
            logger.error(f"Failed to get Redis connection: {e}")
            raise
    
    @staticmethod
    def ping():
        """
        Check if Redis is accessible.
        
        Returns:
            bool: True if Redis is accessible, False otherwise
        """
        try:
            conn = RedisManager.get_connection()
            return conn.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    @staticmethod
    def set_with_expiry(key: str, value: str, ttl: int) -> bool:
        """
        Set a key with expiration time.
        
        Args:
            key: Redis key
            value: Value to store
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            conn = RedisManager.get_connection()
            return conn.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Failed to set key {key} with expiry: {e}")
            return False
    
    @staticmethod
    def get(key: str) -> str:
        """
        Get value by key.
        
        Args:
            key: Redis key
            
        Returns:
            str: Value or None if not found
        """
        try:
            conn = RedisManager.get_connection()
            value = conn.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    @staticmethod
    def delete(key: str) -> bool:
        """
        Delete a key.
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if deleted
        """
        try:
            conn = RedisManager.get_connection()
            return conn.delete(key) > 0
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    @staticmethod
    def exists(key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if exists
        """
        try:
            conn = RedisManager.get_connection()
            return conn.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False

