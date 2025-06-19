import time
import logging

class FirePersistenceTracker:
    def __init__(self, min_duration=5, cooldown=60):
        """
        :param min_duration: Thời gian lửa phải tồn tại liên tục (giây) để được coi là đáng tin cậy
        :param cooldown: Thời gian chờ giữa 2 lần gửi cảnh báo (giây)
        """
        self.fire_states = {}  # dev_id: {fire_start_time, last_alert_time}
        self.min_duration = min_duration
        self.cooldown = cooldown

    def should_send_alert(self, dev_id, is_fire):
        now = time.time()
        state = self.fire_states.setdefault(dev_id, {
            "fire_start_time": None,
            "last_alert_time": 0
        })

        if is_fire:
            if state["fire_start_time"] is None:
                state["fire_start_time"] = now
            elif now - state["fire_start_time"] >= self.min_duration:
                if now - state["last_alert_time"] >= self.cooldown:
                    state["last_alert_time"] = now
                    logging.info(f"🔥 Dev {dev_id}: Lửa liên tục ≥ {self.min_duration}s → GỬI cảnh báo")
                    return True
                else:
                    logging.info(f"⏳ Dev {dev_id}: Đủ điều kiện nhưng còn cooldown ({now - state['last_alert_time']:.1f}s)")
        else:
            state["fire_start_time"] = None  # Lửa bị ngắt

        return False
