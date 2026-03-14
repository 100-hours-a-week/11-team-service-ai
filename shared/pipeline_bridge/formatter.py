import json
import uuid

from taskiq import TaskiqMessage
from taskiq.abc.formatter import TaskiqFormatter, BrokerMessage


class RawJsonFormatter(TaskiqFormatter):
    """
    Spring Boot 서버 등 외부에서 전송한 평문 JSON(Raw JSON)을
    Taskiq가 이해할 수 있는 TaskiqMessage 규격으로 래핑해주는 커스텀 포맷터.
    """

    def __init__(self, default_task_name: str):
        self.default_task_name = default_task_name

    def dumps(self, message: TaskiqMessage) -> BrokerMessage:
        return BrokerMessage(
            task_id=message.task_id,
            task_name=message.task_name,
            labels=message.labels,
            message=message.model_dump_json().encode("utf-8"),
        )

    def loads(self, message: bytes) -> TaskiqMessage:
        try:
            raw_data = json.loads(message.decode("utf-8"))
        except Exception:
            raw_data = {}

        # 이미 TaskiqMessage의 규격(task_id, task_name 등)을 갖추고 있다면 그대로 파싱
        if "task_name" in raw_data and "task_id" in raw_data and "args" in raw_data:
            return TaskiqMessage(**raw_data)

        # 그 외의 일반 JSON 요청이라면, 브로커에 설정된 default_task_name을 이용하여 래핑
        # Pydantic 모델에 파싱되도록 kwargs에 "request" 파라미터로 원본 데이터를 넘겨줌
        return TaskiqMessage(
            task_id=str(uuid.uuid4()),
            task_name=self.default_task_name,
            labels={},
            args=[],
            kwargs={"request": raw_data},
        )
