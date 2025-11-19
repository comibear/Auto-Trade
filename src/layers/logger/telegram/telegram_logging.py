import logging
import asyncio

class TelegramLogHandler(logging.Handler):
    """
    logging.Logger에 붙여서 INFO 이상 메시지를 텔레그램으로 전송
    """
    def __init__(self, notifier):
        super().__init__()
        self.notifier = notifier

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.notifier.send(msg))
        except RuntimeError:
            # 이벤트 루프 없으면 무시(테스트/동기 컨텍스트)
            pass
