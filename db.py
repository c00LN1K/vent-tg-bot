from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func, Float
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine('sqlite:///mydb.db', echo=True)
session = sessionmaker(bind=engine)()


class Base(DeclarativeBase):
    __abstract__ = True

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True, nullable=False, index=True)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


class User(Base):
    __tablename__ = 'users'
    name = Column(String(255), nullable=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    on_work = Column(Boolean, default=False, nullable=False)

    @classmethod
    def check_user(cls, telegram_id):
        return session.query(cls).filter_by(telegram_id=telegram_id, active=True).first()

    @classmethod
    def set_on_work(cls, telegram_id, value):
        session.query(cls).filter_by(telegram_id=telegram_id).update({'on_work': value})
        session.commit()

    @classmethod
    def get_on_work_users(cls):
        return session.query(cls).filter_by(active=True, on_work=True).all()


class Vent(Base):
    __tablename__ = 'vents'
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    temperature = Column(Integer, nullable=False)
    current_flow = Column(Float, nullable=False)
    alarm1 = Column(Boolean, default=False, nullable=False)
    alarm2 = Column(Boolean, default=False, nullable=False)
    alarm3 = Column(Boolean, default=False, nullable=False)

    @classmethod
    def add_record(cls, temperature, current_flow, alarm1, alarm2, alarm3):
        try:
            record = cls(temperature=temperature, current_flow=current_flow, alarm1=alarm1, alarm2=alarm2,
                         alarm3=alarm3)
            session.add(record)
            session.commit()
        except Exception as e:
            print(f'Ошибка при добавлении записи: {e}')
            session.rollback()

    @classmethod
    def get_last_record(cls):
        return session.query(cls).order_by(cls.date.desc()).first()


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
