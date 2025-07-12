import logging
import sys
import signal

from signalwire.relay.consumer import Consumer
from signalwire.relay.calling import Call

# 👇 You can reuse existing config values from your config file
from app.core.config import (
    SIGNALWIRE_PROJECT_ID,
    SIGNALWIRE_API_TOKEN,
    SIGNALWIRE_SPACE_URL
)

SIGNALWIRE_PHONE_NUMBER = '+12092659875'  # 👈 Replace with your real SignalWire number
CLICK2CALL_CONTEXT = 'click2call'         # 👈 Must match your C2C widget destination

logger = logging.getLogger(__name__)

class ClickToCallConsumer(Consumer):
    def setup(self):
        self.project = SIGNALWIRE_PROJECT_ID
        self.token = SIGNALWIRE_API_TOKEN
        self.contexts = [CLICK2CALL_CONTEXT]
        logger.info("📞 Click-to-Call consumer ready!")

    def ready(self):
        logger.info("✅ Click-to-Call connected, listening for widget calls...")

    async def on_incoming_call(self, call: Call):
        logger.info(f"📥 C2C Call from {call.from_number}")
        await call.answer()

        # 👇 Forward this call to your SignalWire phone number (your main pipeline handles it)
        await call.connect({
            "type": "phone",
            "from": call.to_number,
            "to": SIGNALWIRE_PHONE_NUMBER
        })

        logger.info("📤 Forwarded C2C call to SignalWire number")

def setup_signal_handlers(consumer):
    def shutdown(sig, frame):
        logger.info("🛑 Shutting down C2C consumer…")
        consumer.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [C2C] %(levelname)s %(message)s")
    logger.info("🚀 Starting Click-to-Call Relay server")
    agent = ClickToCallConsumer()
    setup_signal_handlers(agent)
    agent.run()

if __name__ == "__main__":
    main()
