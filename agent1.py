import uuid
import atexit
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
)
from prompt1 import AGENT_INSTRUCTION, SESSION_INSTRUCTION
import tools1

load_dotenv()


class Assistant(Agent):
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._session_active = True

        super().__init__(
            instructions=AGENT_INSTRUCTION,
            stt=openai.STT(model="gpt-4o-transcribe"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tools=[
                tools1.log_message,
                tools1.save_session,
                tools1.get_conversation_history,
                tools1.internet_search,
            ],
            tts=openai.TTS(model="gpt-4o-mini-tts", voice="ash"),
            vad=silero.VAD.load()
        )

    async def on_message(self, message, participant, is_final):
        """Handle all incoming messages"""
        if not is_final or not message.strip():
            return
        
        speaker = "user" if not participant.is_local else "assistant"
        print(f"Message received - Speaker: {speaker}, Text: {message}")
        await tools1.log_message(self.session_id, speaker, message)

    async def on_user_speech_committed(self, message):
        """Called when user speech is finalized"""
        if message.content.strip():
            print(f"User speech committed: {message.content}")
            await tools1.log_message(self.session_id, "user", message.content)

    async def on_agent_speech_committed(self, message):
        """Called when agent speech is finalized"""
        if message.content.strip():
            print(f"Agent speech committed: {message.content}")
            await tools1.log_message(self.session_id, "assistant", message.content)

    async def on_function_calls_finished(self, called_functions):
        """Log when functions are called"""
        for func in called_functions:
            if hasattr(func, 'function_info') and func.function_info.name == 'log_message':
                continue  # Skip logging the log_message calls themselves
            print(f"Function called: {func.function_info.name if hasattr(func, 'function_info') else 'unknown'}")

    async def on_user_speech_end(self, text: str):
        """Fallback handler for user speech"""
        if text.strip():
            print(f"User finished: {text}")
            await tools1.log_message(self.session_id, "user", text)

    async def on_agent_speech_end(self, text: str):
        """Fallback handler for agent speech"""  
        if text.strip():
            print(f"Agent finished: {text}")
            await tools1.log_message(self.session_id, "assistant", text)
    
    async def on_session_end(self):
        """Called when the session ends"""
        if self._session_active:
            print(f"Session {self.session_id} ending, saving data...")
            await tools1.save_session(self.session_id)
            self._session_active = False


async def entrypoint(ctx: agents.JobContext):
    session_id = str(uuid.uuid4())
    print(f"Starting finance bot session {session_id}")

    assistant = Assistant(session_id=session_id)
    session = AgentSession()

    # Log the initial message
    await tools1.log_message(session_id, "assistant", "Hello! Ask me about investments or digital gold.")

    # Register cleanup on exit
    def cleanup_session():
        import asyncio
        try:
            if assistant._session_active:
                # Force save session data
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(tools1.save_session(session_id))
                loop.close()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    atexit.register(cleanup_session)

    try:
        await session.start(
            room=ctx.room,
            agent=assistant,
            room_input_options=RoomInputOptions(
                video_enabled=False,
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        # Generate initial reply with session instructions
        await session.generate_reply(
            instructions=f"{SESSION_INSTRUCTION}\n\nSession ID: {session_id}"
        )
        
        # Keep the session alive and handle ongoing conversation
        print(f"Session {session_id} is now active and ready for conversation")
        
    except Exception as e:
        print(f"Session error: {e}")
        await assistant.on_session_end()
        raise
    finally:
        # Ensure session is saved when room disconnects
        print(f"Session {session_id} ending, performing final save...")
        await assistant.on_session_end()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))