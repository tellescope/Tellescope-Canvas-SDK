# Description:
# This protocol automatically forwards Canvas messages to Tellescope chat when a practitioner creates a new message.
# It extracts message content and sender information, then creates corresponding chat messages in Tellescope.

import json
from typing import Optional

from canvas_sdk.effects import Effect, EffectType
from canvas_sdk.events import EventType
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.v1.data import Message, CanvasUser, Staff
from logger import log

from tellescope.utilities.canvas_chat_sender import CanvasChatSender


class Protocol(BaseProtocol):
    """
    Canvas Message to Tellescope Chat Forwarding Protocol
    
    Automatically forwards Canvas messages to Tellescope chat when created by practitioners.
    This enables seamless communication synchronization between Canvas and Tellescope platforms.
    """

    # Respond to message creation events in Canvas
    RESPONDS_TO = EventType.Name(EventType.MESSAGE_CREATED)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize chat sender only if secrets are available
        if self.secrets.get("TELLESCOPE_API_KEY"):
            self.chat_sender = CanvasChatSender()
        else:
            self.chat_sender = None

    def compute(self) -> list[Effect]:
        """
        Handle message creation event by forwarding to Tellescope chat
        """
        # Return early if secrets are not available
        if not self.chat_sender:
            log.warning("Tellescope credentials not configured - skipping chat forwarding")
            return []
            
        try:
            # Get the message instance from the event
            message = self.event.target.instance
            
            if not message:
                log.error("No message instance found in event")
                return self._create_error_effects("Message instance not found")
            
            # Get patient ID from event context
            patient_id = self.event.context.get("patient", {}).get("id")
            if not patient_id:
                log.error("No patient ID found in event context")
                return self._create_error_effects("Patient ID not found in message context")
            
            # Check if message has a sender
            if not message.sender:
                log.debug("Message has no sender - skipping (likely system message)")
                return []
            
            # Check if sender is a practitioner (linked to Staff member)
            if not self._is_practitioner(message.sender):
                log.debug(f"Message sender {message.sender.id} is not a practitioner - skipping")
                return []
            
            # Extract message content
            message_content = getattr(message, 'content', '')
            if not message_content or not message_content.strip():
                log.debug("Message has no content - skipping")
                return []
            
            # Get sender information
            sender_user = message.sender
            sender_id = str(sender_user.id) if sender_user.id else None
            sender_first_name = getattr(sender_user, 'first_name', None)
            sender_last_name = getattr(sender_user, 'last_name', None)
            
            if not sender_id:
                log.error("Could not extract sender ID from message")
                return self._create_error_effects("Sender information not available")
            
            # Convert plain text message to basic HTML if needed
            html_content = self._convert_to_html(message_content)
            
            # Forward message to Tellescope chat
            result = self.chat_sender.send_chat_message(
                canvas_staff_id=sender_id,
                canvas_patient_id=str(patient_id),
                html_message=html_content,
                staff_first_name=sender_first_name,
                staff_last_name=sender_last_name
            )
            
            if result:
                log.info(f"Successfully forwarded Canvas message {message.id} to Tellescope chat")
                return self._create_success_effects("Message forwarded to Tellescope chat")
            else:
                log.warning(f"Patient {patient_id} not found in Tellescope - message not forwarded")
                return []  # No error since patient may not be synced yet
            
        except Exception as e:
            log.error(f"Error forwarding Canvas message to Tellescope: {str(e)}")
            return self._create_error_effects(f"Failed to forward message: {str(e)}")

    def _is_practitioner(self, canvas_user: CanvasUser) -> bool:
        """
        Check if a CanvasUser is a practitioner (linked to a Staff member)
        
        Args:
            canvas_user: CanvasUser to check
            
        Returns:
            True if user is linked to a Staff member, False otherwise
        """
        try:
            # Check if there's a Staff member linked to this CanvasUser
            staff_member = Staff.objects.filter(user=canvas_user).first()
            return staff_member is not None
            
        except Exception as e:
            log.warning(f"Error checking if user {canvas_user.id} is practitioner: {str(e)}")
            # Return False on error to avoid forwarding patient messages
            return False

    def _convert_to_html(self, text_content: str) -> str:
        """
        Convert plain text message content to basic HTML format
        
        Args:
            text_content: Plain text message content
            
        Returns:
            HTML formatted message content
        """
        if not text_content:
            return ""
        
        # Basic text-to-HTML conversion
        # Replace line breaks with HTML line breaks
        html_content = text_content.replace('\n', '<br>')
        
        # Wrap in paragraph tags for proper formatting
        html_content = f"<p>{html_content}</p>"
        
        return html_content

    def _create_success_effects(self, message: str) -> list[Effect]:
        """
        Create success banner alert effects
        
        Args:
            message: Success message to display
            
        Returns:
            List of success effects
        """
        return [Effect(
            type=EffectType.ADD_BANNER_ALERT,
            payload={
                "type": "success",
                "message": message
            }
        )]

    def _create_error_effects(self, error_message: str) -> list[Effect]:
        """
        Create error banner alert effects
        
        Args:
            error_message: Error message to display
            
        Returns:
            List of error effects
        """
        return [Effect(
            type=EffectType.ADD_BANNER_ALERT,
            payload={
                "type": "error",
                "message": f"Chat forwarding error: {error_message}"
            }
        )]