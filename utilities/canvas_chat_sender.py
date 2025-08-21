"""
Canvas Chat Sender Utility

Utility functions for sending chat messages via Tellescope for Canvas Staff/Practitioners.
Handles finding/creating chat rooms and sending messages to Canvas patients.
"""

import json
from typing import Optional, Dict, Any

from tellescope.utilities.tellescope_api import TellescopeAPI
from tellescope.utilities.canvas_enduser_lookup import CanvasEnduserLookup
from tellescope.utilities.canvas_user_lookup import CanvasUserLookup


class CanvasChatSender:
    """
    Utility class for sending chat messages from Canvas Staff to Tellescope patients
    
    Workflow:
    1. Find matching Tellescope Enduser for Canvas patient
    2. Find matching Tellescope User for Canvas Staff (with fallback)
    3. Find or create ChatRoom for the patient
    4. Send ChatMessage in the room
    """

    def __init__(self, tellescope_api: Optional[TellescopeAPI] = None):
        """
        Initialize the chat sender utility
        
        Args:
            tellescope_api: Optional TellescopeAPI instance, creates new one if not provided
        """
        self.tellescope_api = tellescope_api or TellescopeAPI()
        self.enduser_lookup = CanvasEnduserLookup(self.tellescope_api)
        self.user_lookup = CanvasUserLookup(self.tellescope_api)

    def send_chat_message(self, canvas_staff_id: str, canvas_patient_id: str, html_message: str,
                         staff_first_name: Optional[str] = None, staff_last_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Send a chat message from Canvas Staff to Canvas Patient via Tellescope
        
        Args:
            canvas_staff_id: Canvas Staff identifier
            canvas_patient_id: Canvas Patient identifier  
            html_message: HTML content of the message
            staff_first_name: Staff first name (for User lookup fallback)
            staff_last_name: Staff last name (for User lookup fallback)
            
        Returns:
            ChatMessage record if successful, None if patient not found
            
        Raises:
            Exception: If there's an error with the Tellescope API
        """
        try:
            # 1. Load matching Enduser from Tellescope
            enduser = self.enduser_lookup.find_enduser_for_canvas_patient(canvas_patient_id)
            if not enduser:
                # Return early if no enduser found
                return None
            
            enduser_id = enduser["id"]
            
            # 2. Load matching User ensuring a default is returned
            user = self.user_lookup.find_user_for_canvas_practitioner(
                canvas_staff_id=canvas_staff_id,
                first_name=staff_first_name,
                last_name=staff_last_name,
                return_any_if_no_match=True
            )
            
            if not user:
                raise Exception("No Tellescope User found and no fallback available")
            
            user_id = user["id"]
            
            # 3. Find or create ChatRoom for the patient
            chat_room = self._find_or_create_chat_room(canvas_patient_id, enduser_id)
            chat_room_id = chat_room["id"]
            
            # 4. Create ChatMessage in the room
            chat_message = self._create_chat_message(chat_room_id, user_id, html_message)
            
            return chat_message
            
        except Exception as e:
            raise Exception(f"Error sending chat message: {str(e)}")

    def _find_or_create_chat_room(self, canvas_patient_id: str, enduser_id: str) -> Dict[str, Any]:
        """
        Find existing ChatRoom or create new one for Canvas patient
        
        Args:
            canvas_patient_id: Canvas Patient identifier
            enduser_id: Tellescope Enduser ID
            
        Returns:
            ChatRoom record
            
        Raises:
            Exception: If there's an error with the Tellescope API
        """
        try:
            # Look for existing ChatRoom with Canvas source and patient ID
            mongodb_filter = {
                "$and": [
                    {"source": "Canvas"},
                    {"externalId": str(canvas_patient_id)}
                ]
            }
            
            existing_room = self.tellescope_api.find_by("chat-rooms", mongodb_filter)
            
            if existing_room:
                return existing_room
            
            # Create new ChatRoom if none exists
            room_data = {
                "title": "Health Discussion", # generic since Canvas chat can be about anything
                "source": "Canvas",
                "externalId": str(canvas_patient_id),
                "enduserIds": [enduser_id],
                "userIds": []  # Empty array as requested
            }
            
            return self.tellescope_api.create("chat-room", room_data)
            
        except Exception as e:
            raise Exception(f"Error finding or creating chat room: {str(e)}")

    def _create_chat_message(self, chat_room_id: str, sender_user_id: str, html_message: str) -> Dict[str, Any]:
        """
        Create a new ChatMessage in the specified room
        
        Args:
            chat_room_id: ChatRoom ID where message will be sent
            sender_user_id: Tellescope User ID of the sender
            html_message: HTML content of the message
            
        Returns:
            ChatMessage record
            
        Raises:
            Exception: If there's an error with the Tellescope API
        """
        try:
            message_data = {
                "roomId": chat_room_id,
                "senderId": sender_user_id,
                "message": "",
                "html": html_message
            }
            
            return self.tellescope_api.create("chat", message_data)
            
        except Exception as e:
            raise Exception(f"Error creating chat message: {str(e)}")

    def find_chat_room_for_canvas_patient(self, canvas_patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Find existing ChatRoom for Canvas patient
        
        Args:
            canvas_patient_id: Canvas Patient identifier
            
        Returns:
            ChatRoom record if found, None otherwise
            
        Raises:
            Exception: If there's an error with the Tellescope API
        """
        try:
            mongodb_filter = {
                "$and": [
                    {"source": "Canvas"},
                    {"externalId": str(canvas_patient_id)}
                ]
            }
            
            return self.tellescope_api.find_by("chat-rooms", mongodb_filter)
            
        except Exception as e:
            raise Exception(f"Error finding chat room: {str(e)}")

    def get_chat_history_for_canvas_patient(self, canvas_patient_id: str, limit: Optional[int] = 50) -> Optional[Dict[str, Any]]:
        """
        Get chat history for Canvas patient
        
        Args:
            canvas_patient_id: Canvas Patient identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            Dict containing chat room and messages, None if no room found
            
        Raises:
            Exception: If there's an error with the Tellescope API
        """
        try:
            # Find the chat room first
            chat_room = self.find_chat_room_for_canvas_patient(canvas_patient_id)
            if not chat_room:
                return None
            
            # Get messages for the room
            mongodb_filter = {"roomId": chat_room["id"]}
            messages = self.tellescope_api.list("chats", mongodb_filter=mongodb_filter, limit=limit)
            
            return {
                "chat_room": chat_room,
                "messages": messages
            }
            
        except Exception as e:
            raise Exception(f"Error getting chat history: {str(e)}")


# Convenience functions for direct usage without instantiating the class
def send_canvas_chat_message(canvas_staff_id: str, canvas_patient_id: str, html_message: str,
                           staff_first_name: Optional[str] = None, staff_last_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to send a chat message from Canvas Staff to Canvas Patient
    
    Args:
        canvas_staff_id: Canvas Staff identifier
        canvas_patient_id: Canvas Patient identifier
        html_message: HTML content of the message
        staff_first_name: Staff first name (for User lookup fallback)
        staff_last_name: Staff last name (for User lookup fallback)
        
    Returns:
        ChatMessage record if successful, None if patient not found
        
    Raises:
        Exception: If there's an error with the Tellescope API
    """
    sender = CanvasChatSender()
    return sender.send_chat_message(canvas_staff_id, canvas_patient_id, html_message, staff_first_name, staff_last_name)


def find_canvas_patient_chat_room(canvas_patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to find ChatRoom for Canvas patient
    
    Args:
        canvas_patient_id: Canvas Patient identifier
        
    Returns:
        ChatRoom record if found, None otherwise
        
    Raises:
        Exception: If there's an error with the Tellescope API
    """
    sender = CanvasChatSender()
    return sender.find_chat_room_for_canvas_patient(canvas_patient_id)


def get_canvas_patient_chat_history(canvas_patient_id: str, limit: Optional[int] = 50) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get chat history for Canvas patient
    
    Args:
        canvas_patient_id: Canvas Patient identifier
        limit: Maximum number of messages to retrieve
        
    Returns:
        Dict containing chat room and messages, None if no room found
        
    Raises:
        Exception: If there's an error with the Tellescope API
    """
    sender = CanvasChatSender()
    return sender.get_chat_history_for_canvas_patient(canvas_patient_id, limit)