class RegistrationStub:
    def is_valid(self, owner: str) -> bool:
        return len(owner.strip()) >= 3


class AntifraudGateway:
    def notify(self, transfer: dict) -> None:
        return None
