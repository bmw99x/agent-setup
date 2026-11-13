from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    recipient: str


@dataclass(frozen=True)
class EmailMessage(Message):
    subject: str
    body: str


@dataclass(frozen=True)
class SmsMessage(Message):
    text: str
