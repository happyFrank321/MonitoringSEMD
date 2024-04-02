from warnings import filterwarnings
from sqlalchemy.exc import SAWarning

filterwarnings('ignore', category=SAWarning)

import inspect
import sys
import datetime as dt
import typing as t

from sqlalchemy import (
    CHAR, Column, Date, DateTime, Float,
    ForeignKey, String, Text, Time,
    text, BLOB
)
from sqlalchemy.dialects.mysql import (
    INTEGER, SMALLINT, TINYINT, TINYTEXT,
    DECIMAL, BIGINT, LONGTEXT, VARCHAR,
    MEDIUMTEXT
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from core.database import CConnection

def as_dict(cls, columns=None):
    if hasattr(cls, "__tablename__"):
        if columns:
            return {c.name: getattr(cls, c.name) for c in columns}
        else:
            return {c.name: getattr(cls, c.name) for c in cls.__table__.columns}


def checksum(cls):
    checksum = ''

    if hasattr(cls, "__tablename__"):
        connection = CConnection()
        connection.get_session()
        conn = connection.engine.connect()
        result = conn.engine.execute(f"CHECKSUM TABLE {cls.__tablename__};")
        for r in result:
            checksum = str(r.Checksum)

    return checksum


class CRUDModel:
    """ Base CRUD Model class """

    async def save(
            self,
            session: AsyncSession,
            commit=False
    ):
        """
        :param session: your transaction
        :param commit: if commit=False Don't forget to commit by yourself!!!
        """
        await self.before_save()
        async with session as session:
            session.add(self)
            # transfer changes from logic to db transaction
            await session.flush([self])
            if commit:
                await session.commit()

    async def before_save(self):
        """ Set default fields before saving """
        if hasattr(self, 'createDatetime'):
            setattr(self, 'createDatetime', dt.datetime.now())
        if hasattr(self, 'modifyDatetime'):
            setattr(self, 'modifyDatetime', dt.datetime.now())
        if hasattr(self, 'deleted'):
            setattr(self, 'deleted', 0)

    async def update(
            self,
            values: t.Dict[str, t.Any],
            session: AsyncSession,
            commit=False
    ):
        """
        :param session: your transaction
        :param values: {column_name: value}
        :param commit: if commit=False Don't forget to commit by yourself!!!
        """
        for key, value in values:
            if hasattr(self, key):
                setattr(self, key, value)

        await self.before_update()

        async with session as session:
            session.add(self)
            # transfer changes from logic to db transaction
            await session.flush([self])
            if commit:
                await session.commit()

    async def before_update(self):
        """ Set modifyDatetime for updated object """
        if hasattr(self, 'modifyDatetime'):
            setattr(self, 'modifyDatetime', dt.datetime.now())

    async def delete(
            self,
            session: AsyncSession,
            commit=False,
            soft=True
    ):
        """
        :param session: your transaction
        :param soft: if True: set deleted = 1 to the object, else delete the object
        :param commit: if commit=False Don't forget to commit by yourself!!!
        """
        async with session as session:
            if soft:
                if hasattr(self, 'deleted'):
                    await self.before_update()
                    setattr(self, 'deleted', 0)

                    session.add(self)
                    await session.flush([self])
            else:
                await session.delete(self)
            if commit:
                await session.commit()


Base = declarative_base(cls=CRUDModel)
metadata = Base.metadata
Base.as_dict = as_dict


class KLADR(Base):
    __tablename__ = 'KLADR'

    NAME = Column(String(40), nullable=False)
    SOCR = Column(String(10), nullable=False)
    CODE = Column(String(13), primary_key=True)
    INDEX = Column(String(6), nullable=False)
    GNINMB = Column(String(4), nullable=False)
    UNO = Column(String(4), nullable=False)
    OCATD = Column(String(11), nullable=False)
    STATUS = Column(String(1), nullable=False)
    parent = Column(String(13), nullable=False)
    infis = Column(String(5), nullable=False)
    prefix = Column(String(2), nullable=False)
    isInsuranceArea = Column(TINYINT(1), nullable=False, server_default=text("0"),
                             comment='Является территорией страхования')


class MKB(Base):
    __tablename__ = 'MKB'

    id = Column(INTEGER(11), primary_key=True)
    ClassID = Column(String(8), nullable=False)
    ClassName = Column(String(150), nullable=False)
    BlockID = Column(String(9), nullable=False)
    BlockName = Column(String(160), nullable=False)
    DiagID = Column(String(8), nullable=False)
    DiagName = Column(String(160), nullable=False)
    Prim = Column(String(1), nullable=False)
    sex = Column(TINYINT(1), nullable=False)
    age = Column(String(12), nullable=False)
    characters = Column(TINYINT(4), nullable=False)
    duration = Column(INTEGER(4), nullable=False)
    service_id = Column(INTEGER(11), comment='Базовый сервис ОМС {rbService}')
    MKBSubclass_id = Column(INTEGER(11), comment='Субклассификация по пятому знаку {rbMKBSubclass}')
    OMS = Column(TINYINT(1), server_default=text("1"), comment='Краевой')
    MTR = Column(TINYINT(1), server_default=text("1"), comment='Инокраевой')
    begDate = Column(Date, nullable=False, comment='Дата начала действия')
    endDate = Column(Date, nullable=False, comment='Дата окончания действия')
    USL_OK1 = Column(TINYINT(1), nullable=False, server_default=text("0"),
                     comment='Использование в стационаре (0-не оплачивается, 1-оплачивается)')
    USL_OK2 = Column(TINYINT(1), nullable=False, server_default=text("0"),
                     comment='Использование в дневном стационаре (0-не оплачивается, 1-оплачивается)')
    USL_OK3 = Column(TINYINT(1), nullable=False, server_default=text("0"),
                     comment='Использование в поликлинике (0-не оплачивается, 1-оплачивается)')
    USL_OK4 = Column(TINYINT(1), nullable=False, server_default=text("0"),
                     comment='Использование в скорой помощи (0-не оплачивается, 1-оплачивается)')
    SELF = Column(TINYINT(1), nullable=False, server_default=text("0"),
                  comment='Самостоятельный код (возможность быть основным диагнозом в случае лечения) (0-не самостоятельный, 1-самостоятельный)')
    ID_EIS = Column(INTEGER(11), comment='Ид из справочника диагнозов ЕИС')


class Organisation(Base):
    __tablename__ = 'Organisation'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(INTEGER(11), comment='????? ?????? {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(INTEGER(11), comment='????? ????????? ?????? {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("'0'"), comment='??????? ???????? ??????')
    fullName = Column(String(250), nullable=False, comment='?????? ????????????')
    shortName = Column(String(64), nullable=False, comment='??????? ????????????')
    title = Column(String(64), nullable=False, comment='???????????? ??? ??????')
    net_id = Column(ForeignKey('rbNet.id', ondelete='SET NULL'),
                    comment='???? ???????????? NULL ??? ????????????? ??????????? {rbNet}')
    infisCode = Column(String(12), nullable=False, comment='??? ?? ????? (???.????)')
    obsoleteInfisCode = Column(String(60), nullable=False, comment='"????????????" ????? ????')
    OKVED = Column(String(64), nullable=False, comment='?????')
    INN = Column(String(15), nullable=False, comment='???')
    KPP = Column(String(15), nullable=False, comment='???')
    OGRN = Column(String(15), nullable=False, comment='????')
    OKATO = Column(String(15), nullable=False, comment='?????')
    # OKPF_code = Column(String(4), nullable=False, comment='???? - ???, ??????? ????? ??????????? OKPF_id ')
    # OKPF_id = Column(INTEGER(11), comment='???? {rbOKPF}')
    # OKFS_code = Column(INTEGER(11), nullable=False, comment='???? - ???, ??????? ????? ??????????? OKFS_id')
    OKFS_id = Column(INTEGER(11), comment='???? {rbOKFS}')
    OKPO = Column(String(15), nullable=False, comment='????')
    FSS = Column(String(10), nullable=False, comment='???.??? ? ???')
    region = Column(String(25), nullable=False, comment='????? (?)')
    Address = Column(String(250), nullable=False, comment='?????')
    chief = Column(String(64), nullable=False, comment='????????????')
    phone = Column(String(64), nullable=False, comment='???????')
    accountant = Column(String(64), nullable=False, comment='??.?????????')
    isInsurer = Column(TINYINT(1), nullable=False, comment='???????? ????????? ?????????')
    isCompulsoryInsurer = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                                 comment='???????? ????????? ????????? ???')
    isVoluntaryInsurer = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                                comment='???????? ????????? ????????? ???')
    compulsoryServiceStop = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                                   comment='???: 0-?????????????, 1-?????????????? ????????????')
    voluntaryServiceStop = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                                  comment='???: 0-?????????????, 1-?????????????? ????????????')
    area = Column(String(13), nullable=False, comment='?????-??? ??????? ????????? ????????')
    isHospital = Column(TINYINT(1), nullable=False, server_default=text("'0'"), comment='???????? ???????????')
    notes = Column(TINYTEXT, nullable=False, comment='??????????')
    head_id = Column(INTEGER(11), comment='???????? ??????????? {Organisation}')
    miacCode = Column(String(10), nullable=False, comment='??? ? ????')
    isMedical = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                       comment='??? ???????????(0-????????????,1-???????????,2-?????????,3-?????? ???.???????????)')
    isArmyOrg = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                       comment='??????????, ???????? ?? ??????????? ???????????')
    canOmitPolicyNumber = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                                 comment='?? ??????? ???????? ????? ? ?????? ?????? (0 - ???, 1 - ??)')
    netrica_Code = Column(String(64), comment='????????????? ?? ? ??????????? ???????')
    DATN = Column(Date, nullable=False, server_default=text("'2000-01-01'"), comment='???? ????????? ? ????? ???')
    DATO = Column(Date, nullable=False, server_default=text("'2200-01-01'"), comment='???? ?????????? ?? ????? ???')
    reestrNumber = Column(INTEGER(10))
    EGISZ_code = Column(String(512), nullable=False, comment='????????????')

    net = relationship('RbNet')


class OrgStructure(Base):
    __tablename__ = 'OrgStructure'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    organisation_id = Column(INTEGER(11), nullable=False, comment='ЛПУ {Organisation}')
    code = Column(String(64), nullable=False, comment='Код подразделения')
    name = Column(String(256), nullable=False, comment='Наименование')
    parent_id = Column(ForeignKey('OrgStructure.id'), comment='Вышестоящее подразделение {OrgStructure}')
    type = Column(INTEGER(11), nullable=False, server_default=text("0"),
                  comment='Тип (предопределенные значения: "Амбулатория","Стационар","Скорая помощь","Мобильная станция","Приемное отделение стационара")')
    net_id = Column(ForeignKey('rbNet.id', ondelete='SET NULL'), comment='Сеть прикрепления {rbNet}')
    chief_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Зав.отделением {Person}')
    headNurse_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Старшая медсестра {Person}')
    isArea = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='Является участком')
    hasHospitalBeds = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Имеет койки')
    hasStocks = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Подразделение имеет склад')
    hasDayStationary = Column(TINYINT(1), nullable=False, server_default=text("0"))
    infisCode = Column(String(16), nullable=False)
    infisInternalCode = Column(String(30), nullable=False)
    infisDepTypeCode = Column(String(30), nullable=False)
    infisTariffCode = Column(String(16), nullable=False, comment='Селектор тарифа для ИНФИС (HSOBJECT)')
    availableForExternal = Column(INTEGER(1), nullable=False, server_default=text("1"),
                                  comment='Доступно для внешних систем (инфоматов и пр.)')
    address = Column(String(250), nullable=False, comment='Адрес')
    inheritEventTypes = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Наследует типы событий')
    inheritActionTypes = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Наследует типы действий')
    inheritGaps = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Наследует перерывы')
    bookkeeperCode = Column(String(16), nullable=False, comment='Код для связи с ИС БУХУЧЕТА ЛПУ')
    dayLimit = Column(TINYINT(3), comment='лимит мест для госпитализации')
    storageCode = Column(String(64), nullable=False, comment='Код склада подразделения')
    miacHead_id = Column(INTEGER(11), comment='Подразделение для выгрузки infisCode при экспорте в МИАЦ')
    salaryPercentage = Column(INTEGER(11), server_default=text("0"), comment='Процент начисления з/п (i3123)')
    attachCode = Column(INTEGER(10), comment='Код прикрепления')
    isVisibleInDR = Column(TINYINT(4), server_default=text("1"), comment='Видимость подразделения в DoctorRoom')
    tfomsCode = Column(String(16), comment='Код отделения в ТФОМС')
    syncGUID = Column(Text)
    quota = Column(TINYINT(3), server_default=text("0"), comment='Квота для внешних систем')
    miacCode = Column(String(11), comment='код МИАЦ')
    netrica_Code = Column(String(64), comment='Идентификатор подразделения в справочнике Нетрики')
    idLPU_egisz = Column(INTEGER(11), comment='idLPU в сервисе ЕГИСЗ(проставляется для подраз-я и его детей)')
    netrica_Code_IEMK = Column(String(64))
    idxLocationCard = Column(INTEGER(11), server_default=text("0"), comment='Порядок отображения филиалов')
    isVisibleInLocationCard = Column(TINYINT(1), server_default=text("1"),
                                     comment='1 - ФИЛИАЛ виден в списке филиалов для места нахождения амбулаторной карты , 0 - филиал не виден')

    chief = relationship('Person', primaryjoin='OrgStructure.chief_id == Person.id')
    createPerson = relationship('Person', primaryjoin='OrgStructure.createPerson_id == Person.id')
    headNurse = relationship('Person', primaryjoin='OrgStructure.headNurse_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='OrgStructure.modifyPerson_id == Person.id')
    net = relationship('RbNet')
    parent = relationship('OrgStructure', remote_side=[id])


class OrgStructureAncestors(Base):
    __tablename__ = 'OrgStructure_Ancestors'

    id = Column(INTEGER(11), primary_key=True)
    fullPath = Column(String(150), comment='Полный список родителей сверху вниз')


class OrgStructureHospitalBed(Base):
    __tablename__ = 'OrgStructure_HospitalBed'

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(ForeignKey('OrgStructure.id', ondelete='CASCADE'), nullable=False,
                       comment='Подразделение к которому относится койка {OrgStructure}')
    idx = Column(INTEGER(11), nullable=False, server_default=text("0"),
                 comment='относительный индекс (для сортировки в списке)')
    code = Column(String(16), nullable=False, server_default=text("''"), comment='Идентификатор (место)')
    name = Column(String(64), nullable=False, server_default=text("''"), comment='Расшифровка')
    isPermanent = Column(TINYINT(1), nullable=False, server_default=text("0"),
                         comment='флаг является/не является штатной')
    type_id = Column(ForeignKey('rbHospitalBedType.id'), comment='Тип {rbHospitalBedType}')
    profile_id = Column(ForeignKey('rbHospitalBedProfile.id'), comment='Профиль {rbHospitalBedProfile}')
    relief = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='Смены')
    schedule_id = Column(ForeignKey('rbHospitalBedShedule.id'), comment='Режим {rbHospitalBedShedule}')
    begDate = Column(Date, comment='начало периода действия')
    endDate = Column(Date, comment='окончание периода действия')
    sex = Column(TINYINT(4), nullable=False, server_default=text("0"),
                 comment='Применимо для указанного пола (0-любой, 1-М, 2-Ж)')
    age = Column(String(9), nullable=False,
                 comment='Применимо для указанного интервала возрастов пусто-нет ограничения, "{NNN{д|н|м|г}-{MMM{д|н|м|г}}" - с NNN дней/недель/месяцев/лет по MMM дней/недель/месяцев/лет; пустая нижняя или верхняя граница - нет ограничения снизу или сверху')
    involution = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='(deprecated, moved to HospitalBed_Involute.involuteType) Причина сворачивания (0-нет сворачивания,1-ремонт,2- карантин)')
    begDateInvolute = Column(Date,
                             comment='(deprecated, moved to HospitalBed_Involute.begDateInvolute) Дата начала сворачивания')
    endDateInvolute = Column(Date,
                             comment='(deprecated, moved to HospitalBed_Involute.endDateInvolute) Дата окончания сворачивания')
    ward = Column(String(16), nullable=False, server_default=text("''"), comment='Номер палаты')
    paidFlag = Column(TINYINT(1), server_default=text("0"), comment='Признак платной койки подразделения')

    master = relationship('OrgStructure')
    profile = relationship('RbHospitalBedProfile')
    schedule = relationship('RbHospitalBedShedule')
    type = relationship('RbHospitalBedType')


class RbPost(Base):
    __tablename__ = 'rbPost'
    __table_args__ = {'comment': 'Должность; см. MEDPOST.DBF'}

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    code = Column(String(8), nullable=False)
    flatCode = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)
    regionalCode = Column(String(8), nullable=False)
    federalCode = Column(String(16), nullable=False)
    key = Column(String(6), nullable=False)
    high = Column(String(6), nullable=False)
    syncGUID = Column(String(36))
    netrica_Code = Column(String(64))
    row_code = Column(String(10))
    netrica_ZPV = Column(String(64))
    netrica_Code_IEMK = Column(String(64))
    EGISZ_code = Column(String(16))
    EGISZ_name = Column(Text)
    # code_id = Column(String(64))
    role = Column(String(64))

    createPerson = relationship('Person', primaryjoin='RbPost.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbPost.modifyPerson_id == Person.id')


class Person(Base):
    __tablename__ = 'Person'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    code = Column(String(12), nullable=False, comment='Код')
    federalCode = Column(String(16), nullable=False, comment='Какой-то федеральный код')
    regionalCode = Column(String(16), nullable=False, comment='Какой-то региональный код')
    lastName = Column(String(30), nullable=False, comment='Фамилия')
    firstName = Column(String(30), nullable=False, comment='Имя')
    patrName = Column(String(30), nullable=False, comment='Отчество')
    post_id = Column(ForeignKey('rbPost.id'), comment='Должность {rbPost}')
    speciality_id = Column(ForeignKey('rbSpeciality.id'), comment='Специальность {rbSpeciality}')
    org_id = Column(ForeignKey('Organisation.id'), comment='Место работы {Organisation}')
    orgStructure_id = Column(ForeignKey('OrgStructure.id'), comment='Организационная структура {OrgStructure}')
    office = Column(String(8), nullable=False, comment='Кабинет')
    office2 = Column(String(8), nullable=False, comment='Кабинет2')
    tariffCategory_id = Column(INTEGER(11), comment='Тарифная категория {rbTariffCategory}')
    finance_id = Column(ForeignKey('rbFinance.id'), comment='Тип финансирования для Visit {rbFinance}')
    retireDate = Column(Date, comment='Дата, после которой на сотрудника нельзя подавать сведения')
    ambPlan = Column(SMALLINT(4), nullable=False, comment='Количество человек на весь амбулаторный приём')
    ambPlan2 = Column(SMALLINT(4), nullable=False, comment='Количество человек на весь амбулаторный приём')
    ambNorm = Column(SMALLINT(4), nullable=False, comment='Норма амбулаторного приёма на 1 час')
    homPlan = Column(SMALLINT(4), nullable=False, comment='Количество человек на весь д.приём')
    homPlan2 = Column(SMALLINT(4), nullable=False, comment='Количество человек на вызов')
    homNorm = Column(SMALLINT(4), nullable=False, comment='Норма д.приёма на 1 час')
    expPlan = Column(SMALLINT(4), nullable=False, comment='Количество человек на экспертизу')
    expNorm = Column(SMALLINT(4), nullable=False, comment='Норма экспертизы на 1 час')
    login = Column(String(32), nullable=False, comment='имя для входа в систему')
    password = Column(String(64), nullable=False, server_default=text("''"), comment='hash от пароля')
    userProfile_id = Column(INTEGER(11),
                            comment='(deprecated in r16290, see Person_UserProfile) Ссылка на профиль прав доступа {rbUserProfile}')
    retired = Column(TINYINT(1), nullable=False, comment='Вход в систему запрещён')
    birthDate = Column(Date, nullable=False, comment='Дата рождения')
    birthPlace = Column(String(64), nullable=False, comment='Место рождения')
    sex = Column(TINYINT(4), nullable=False, comment='Пол (0-неопределено, 1-М, 2-Ж)')
    SNILS = Column(CHAR(11), nullable=False, comment='СНИЛС')
    INN = Column(CHAR(15), nullable=False, comment='ИНН')
    availableForExternal = Column(INTEGER(1), nullable=False, server_default=text("1"),
                                  comment='Доступно для внешних систем (инфоматов и пр.)')
    lastAccessibleTimelineDate = Column(Date, comment='Последняя доступная дата в расписании врача')
    timelineAccessibleDays = Column(INTEGER(11), nullable=False, server_default=text("0"),
                                    comment='Количество дней, на которые доступно расписание врача')
    canSeeDays = Column(INTEGER(11), nullable=False, server_default=text("0"),
                        comment='Ограничение количества дней, на которое пользователь может видеть чье-либо расписание. (0 - нет ограничения)')
    academicDegree = Column(TINYINT(4), nullable=False, comment='Ученая степень (0-неопределено, 1-к.м.н, 2-д.м.н)')
    typeTimeLinePerson = Column(INTEGER(11), nullable=False, comment='Тип персонального графика')
    addComment = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='флаг необходимости добавления комментария пользователя')
    commentText = Column(String(200), comment='Текст комментария пользователя')
    maritalStatus = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='Состояние в браке (ОКИН 10)')
    contactNumber = Column(String(15), nullable=False, server_default=text("''"), comment='Телефон')
    regType = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Тип регистрации')
    regBegDate = Column(Date, comment='Дата начала регистрации')
    regEndDate = Column(Date, comment='Дата окончания регистрации')
    isReservist = Column(TINYINT(1), nullable=False, server_default=text("0"),
                         comment='Военнообязан (0-не известно, 1-нет, 2-да)')
    employmentType = Column(TINYINT(1), nullable=False, server_default=text("0"),
                            comment='Режим работы (0-не известно, 1-постоянно, 2-временно, 3-по срочному договору)')
    occupationType = Column(TINYINT(1), nullable=False, server_default=text("0"),
                            comment='Тип занятия должности (0-не известно, 1-основное, 2-совмещение)')
    citizenship_id = Column(ForeignKey('rbCitizenship.id'), comment='Гражданство {rbCitizenship}')
    isDefaultInHB = Column(TINYINT(1), nullable=False, server_default=text("1"),
                           comment='0 - не фильтровать; 1 - фильтровать')
    isInvestigator = Column(TINYINT(1), comment='Является главным исследователем')
    syncGUID = Column(String(36), comment='Используется при синхронизации справочников в 1С')
    qaLevel = Column(TINYINT(4), server_default=text("0"),
                     comment='Уровень внутренного контроля качества {0: не задано, 1: первый, 2: второй, 3: врачебная комиссия}')
    signature_cert = Column(Text, comment='Сертификат электронной подписи в формате PEM')
    signature_key = Column(Text, comment='Приватный ключ электронной подписи в формате PEM')
    doctorRoomAccessDenied = Column(TINYINT(1), server_default=text("0"), comment='Вход в DoctorRoom запрещен')
    cashier_code = Column(INTEGER(11), comment='ID кассира')
    mse_speciality_id = Column(INTEGER(4))
    ecp_password = Column(String(100), server_default=text("''"), comment='Пароль от ЭЦП (если есть)')
    grkmGUID = Column(String(45), comment='GUID врача ГРКМ')
    # qualification = Column(String(100), server_default=text("''"), comment='Квалификация Врача')
    # defaultPrinter_id = Column(ForeignKey('OrgStructure_Printers.id', ondelete='SET NULL', onupdate='CASCADE'), comment='Дефолтный принтер штрих-кодов для сотрудника {OrgStructure_Printers}')
    # ready_to_online_consultation = Column(INTEGER(11), server_default=text("0"))
    email = Column(String(20), comment='E-mail')
    disableSignDoc = Column(TINYINT(1), server_default=text("0"), comment='Запрещать подписывать документы этого врача')
    # tadam_username = Column(String(100), comment='логин аккаунта в TADAM')
    # tadam_password = Column(String(20), comment='Временный пароль в ТАДАМ, созданный при генерации аккаунтов')

    citizenship = relationship('RbCitizenship', primaryjoin='Person.citizenship_id == RbCitizenship.id')
    createPerson = relationship('Person', remote_side=[id], primaryjoin='Person.createPerson_id == Person.id')
    # defaultPrinter = relationship('OrgStructurePrinter')
    finance = relationship('RbFinance', primaryjoin='Person.finance_id == RbFinance.id')
    modifyPerson = relationship('Person', remote_side=[id], primaryjoin='Person.modifyPerson_id == Person.id')
    orgStructure = relationship('OrgStructure', primaryjoin='Person.orgStructure_id == OrgStructure.id')
    org = relationship('Organisation')
    post = relationship('RbPost', primaryjoin='Person.post_id == RbPost.id')
    speciality = relationship('RbSpeciality', primaryjoin='Person.speciality_id == RbSpeciality.id')


class RbCaseCast(Base):
    __tablename__ = 'rbCaseCast'

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(6), nullable=False, comment='???')
    name = Column(String(128), nullable=False, comment='????????')


class RbCitizenship(Base):
    __tablename__ = 'rbCitizenship'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(4), nullable=False, server_default=text("''"), comment='???')
    name = Column(String(80), nullable=False, comment='???????? ??????')

    createPerson = relationship('Person', primaryjoin='RbCitizenship.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbCitizenship.modifyPerson_id == Person.id')


class RbContactType(Base):
    __tablename__ = 'rbContactType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    mask = Column(String(64), server_default=text("''"), comment='Маска')
    maskEnabled = Column(TINYINT(1), server_default=text("0"), comment='Применять маску')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.27')

    createPerson = relationship('Person', primaryjoin='RbContactType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbContactType.modifyPerson_id == Person.id')


class RbDistrict(Base):
    __tablename__ = 'rbDistrict'

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(16), nullable=False, comment='Код района')
    name = Column(String(128), nullable=False, comment='Имя района')


class RbFinance(Base):
    __tablename__ = 'rbFinance'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(8), nullable=False, comment='???')
    name = Column(String(64), nullable=False, comment='????????????')
    idx = Column(INTEGER(11), server_default=text("'0'"), comment='???? ??? ??????????')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.32')
    netricaCode = Column(String(64), comment='netricaCode')

    createPerson = relationship('Person', primaryjoin='RbFinance.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbFinance.modifyPerson_id == Person.id')


class RbInfoSource(Base):
    __tablename__ = 'rbInfoSource'

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(16), nullable=False, comment='??? ?????????')
    name = Column(String(256), nullable=False, comment='???????? ?????????')


class RbMedicalAidKind(Base):
    __tablename__ = 'rbMedicalAidKind'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(8), nullable=False, comment='???')
    name = Column(String(64), nullable=False, comment='????????????')
    regionalCode = Column(String(8), nullable=False, comment='???????????? ???')
    federalCode = Column(String(16), nullable=False, comment='??????????? ???')
    netrica_Code = Column(String(64), comment='????????????? ?? ? ??????????? ???????')

    createPerson = relationship('Person', primaryjoin='RbMedicalAidKind.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbMedicalAidKind.modifyPerson_id == Person.id')


class RbMedicalAidProfile(Base):
    __tablename__ = 'rbMedicalAidProfile'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(16), nullable=False, comment='???')
    regionalCode = Column(String(16), nullable=False, comment='???????????? ???')
    federalCode = Column(String(16), nullable=False, comment='??????????? ??? (?? 79 ???????)')
    name = Column(String(255))
    netrica_Code = Column(String(64), comment='????????????? ?? ? ??????????? ???????')
    netrica_Code3 = Column(String(64))
    netrica_Code2 = Column(String(64), comment='????????????? ????-?? ? ??????????? ???????')

    createPerson = relationship('Person', primaryjoin='RbMedicalAidProfile.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbMedicalAidProfile.modifyPerson_id == Person.id')


class RbMedicalAidType(Base):
    __tablename__ = 'rbMedicalAidType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(8), nullable=False, comment='???')
    name = Column(String(64), nullable=False, comment='????????????')
    regionalCode = Column(String(8), nullable=False, comment='???????????? ???')
    federalCode = Column(String(16), nullable=False, comment='??????????? ??? (?? 79 ???????)')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.25')
    dispStage = Column(INTEGER(11), comment='???? ???????????????')

    createPerson = relationship('Person', primaryjoin='RbMedicalAidType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbMedicalAidType.modifyPerson_id == Person.id')


class RbNet(Base):
    __tablename__ = 'rbNet'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(8), nullable=False, comment='???')
    name = Column(String(64), nullable=False, comment='????????????')
    sex = Column(TINYINT(4), nullable=False, server_default=text("'0'"),
                 comment='????????? ??? ?????????? ???? (0-?????, 1-?, 2-?)')
    age = Column(String(9), nullable=False,
                 comment='????????? ??? ?????????? ????????? ????????? ?????-??? ???????????, "{NNN{?|?|?|?}-{MMM{?|?|?|?}}" - ? NNN ????/??????/???????/??? ?? MMM ????/??????/???????/???; ?????? ?????? ??? ??????? ??????? - ??? ??????????? ????? ??? ??????')
    flags = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                   comment='1 - ????????? ??????????? ???? ??? ??????????? ????????.')

    createPerson = relationship('Person', primaryjoin='RbNet.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbNet.modifyPerson_id == Person.id')


class RbService(Base):
    __tablename__ = 'rbService'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    group_id = Column(ForeignKey('rbServiceGroup.id', ondelete='SET NULL', onupdate='CASCADE'),
                      comment='?????? ????? {rbServiceGroup}')
    code = Column(String(31), nullable=False, comment='???')
    name = Column(String(500), nullable=False, comment='????????????')
    eisLegacy = Column(TINYINT(1), nullable=False, comment='???????????? ?? ???')
    nomenclatureLegacy = Column(TINYINT(1), nullable=False, server_default=text("'0'"),
                                comment='???????????? ?? ???????????? ?????????')
    license = Column(TINYINT(1), nullable=False,
                     comment='??????? ????????????? ???????? (0: ?? ?????????, 1:????????? ????????, 2:????????? ???????????? ??????????)')
    infis = Column(String(31), nullable=False)
    begDate = Column(Date, nullable=False, server_default=text("'2000-01-01'"), comment='????????? ????')
    endDate = Column(Date, nullable=False, server_default=text("'2200-01-01'"), comment='???????? ????')
    medicalAidProfile_id = Column(ForeignKey('rbMedicalAidProfile.id', ondelete='SET NULL'),
                                  comment='??????? ?????? ?? ????????? {rbMedicalAidProfile}')
    medicalAidKind_id = Column(ForeignKey('rbMedicalAidKind.id', ondelete='SET NULL'),
                               comment='??? ?????? {rbMedicalAidKind}')
    medicalAidType_id = Column(ForeignKey('rbMedicalAidType.id', ondelete='SET NULL'),
                               comment='??? ?????? (??? ???????? ??????? ? ???????? ????? ?????????... ) {rbMedicalAidType}')
    adultUetDoctor = Column(Float(asdecimal=True), server_default=text("'0'"),
                            comment='???????? ??? (???????? ??????? ???????????) ??? ?????')
    adultUetAverageMedWorker = Column(Float(asdecimal=True), server_default=text("'0'"),
                                      comment='???????? ??? (???????? ??????? ???????????) ??? ???????? ???????????? ?????????')
    childUetDoctor = Column(Float(asdecimal=True), server_default=text("'0'"),
                            comment='??????? ??? (???????? ??????? ???????????) ??? ?????')
    childUetAverageMedWorker = Column(Float(asdecimal=True), server_default=text("'0'"),
                                      comment='??????? ??? (???????? ??????? ???????????) ??? ???????? ???????????? ?????????')
    qualityLevel = Column(Float(asdecimal=True), nullable=False, server_default=text("'1'"),
                          comment='??????? ???????? ???????')
    superviseComplexityFactor = Column(Float(asdecimal=True), nullable=False, server_default=text("'1'"),
                                       comment='??????????? ????????? ???????')
    tarif = Column(String(255))
    gr = Column(String(255))
    category_id = Column(INTEGER(11), comment='????????? ??????')
    caseCast_id = Column(ForeignKey('rbCaseCast.id', onupdate='CASCADE'), comment='????????? ??????')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.29')
    Fed_code = Column(String(30), comment='???. ??? ??????')

    caseCast = relationship('RbCaseCast')
    createPerson = relationship('Person', primaryjoin='RbService.createPerson_id == Person.id')
    group = relationship('RbServiceGroup')
    medicalAidKind = relationship('RbMedicalAidKind')
    medicalAidProfile = relationship('RbMedicalAidProfile')
    medicalAidType = relationship('RbMedicalAidType')
    modifyPerson = relationship('Person', primaryjoin='RbService.modifyPerson_id == Person.id')


class RbServiceGroup(Base):
    __tablename__ = 'rbServiceGroup'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(16), nullable=False, server_default=text("''"), comment='???')
    regionalCode = Column(String(16), nullable=False, server_default=text("''"), comment='???')
    name = Column(String(128), nullable=False, comment='????????????')

    createPerson = relationship('Person', primaryjoin='RbServiceGroup.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbServiceGroup.modifyPerson_id == Person.id')


class RbSpeciality(Base):
    __tablename__ = 'rbSpeciality'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(8), nullable=False, comment='???')
    name = Column(String(64), nullable=False, comment='????????????')
    OKSOName = Column(String(60), nullable=False)
    OKSOCode = Column(String(8), nullable=False)
    federalCode = Column(String(16), nullable=False, comment='??????????? ??? (?? 79 ???????)')
    service_id = Column(ForeignKey('rbService.id'), comment='??????? ?????? ??? {rbService}')
    provinceService_id = Column(ForeignKey('rbService.id', ondelete='SET NULL', onupdate='CASCADE'),
                                comment='?????? ??? ??? ?????????? ????????? {rbService}')
    otherService_id = Column(ForeignKey('rbService.id', ondelete='SET NULL', onupdate='CASCADE'),
                             comment='??????  ??? ??? ??????? ????????? {rbService}')
    sex = Column(TINYINT(4), nullable=False, comment='?????? ?????? ???????? ??? ?????????? ???? (0-?????, 1-?, 2-?)')
    age = Column(String(9), nullable=False,
                 comment='?????? ?????? ???????? ????????? ????????? ?????-??? ???????????, "{NNN{?|?|?|?}-{MMM{?|?|?|?}}" - ? NNN ????/??????/???????/??? ?? MMM ????/??????/???????/???; ?????? ?????? ??? ??????? ??????? - ??? ??????????? ????? ??? ??????')
    mkbFilter = Column(String(32), nullable=False, comment='?????? ?????? ???')
    regionalCode = Column(String(16), nullable=False, comment='???????????? ???')
    shortName = Column(String(64), comment='??????? ????????????')
    versSpec = Column(String(8), nullable=False, server_default=text("''"),
                      comment='?????? (????????????) ??????????? (V004/V015) ??? ?????? ?? ??. 79')
    syncGUID = Column(String(36), comment='???????????? ??? ????????????? ???????????? ? 1?')
    netrica_Code = Column(String(64), comment='????????????? ?? ? ??????????? ???????')
    fundingService_id = Column(ForeignKey('rbService.id', onupdate='CASCADE'),
                               comment='?????? ??? ?????????? ??????????????')
    shouldFillOncologyForm90 = Column(TINYINT(1), server_default=text("'0'"),
                                      comment='???????????? ?????? ????????? ????? 90 ??? ?????????? ????????? ????????? ??? ???????? ?????????? ????????? 71')
    queueShareMode = Column(TINYINT(1), server_default=text("'0'"), comment='????? "?????-???????"')
    kind = Column(INTEGER(11), server_default=text("'0'"), comment='??? ?????????????')

    createPerson = relationship('Person', primaryjoin='RbSpeciality.createPerson_id == Person.id')
    fundingService = relationship('RbService', primaryjoin='RbSpeciality.fundingService_id == RbService.id')
    modifyPerson = relationship('Person', primaryjoin='RbSpeciality.modifyPerson_id == Person.id')
    otherService = relationship('RbService', primaryjoin='RbSpeciality.otherService_id == RbService.id')
    provinceService = relationship('RbService', primaryjoin='RbSpeciality.provinceService_id == RbService.id')
    service = relationship('RbService', primaryjoin='RbSpeciality.service_id == RbService.id')


class RbPrintTemplate(Base):
    __tablename__ = 'rbPrintTemplate'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(16), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    context = Column(String(64), nullable=False, comment='Контекст (order, token, F131 и т.п.) ')
    fileName = Column(String(128), nullable=False, comment='Имя файла шаблона')
    default = Column(MEDIUMTEXT)
    dpdAgreement = Column(TINYINT(1), nullable=False, server_default=text("0"),
                          comment='Меняет ли ДПД клиента при печати: 0-Не меняет, 1-Меняет на "Да", 2-Меняет на "Нет" ')
    type = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Тип шаблона: 0-HTML,1-Exaro,2-SVG')
    banUnkeptDate = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='0=разрешено, 1=запрещено')
    counter_id = Column(ForeignKey('rbCounter.id'), comment='Используемый счетчик при печати из обращений')
    deleted = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='отметка об удалении')
    isPatientAgreed = Column(TINYINT(1), server_default=text("0"), comment='Необходимость согласования с клиентом')
    groupName = Column(String(20), comment='Группа')
    documentType_id = Column(ForeignKey('rbIEMKDocument.id'), comment='Тип документа по ИЭМК')
    hideParam = Column(TINYINT(1), comment='2-скрыть у врачей')
    isEditableInWeb = Column(TINYINT(1), nullable=False, server_default=text("1"))
    chkProfiles = Column(TINYINT(1), nullable=False, server_default=text("0"),
                         comment='Доступно только определённым правам пользователей')
    chkPersons = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='Доступно только определённым пользователям')
    sendMail = Column(TINYINT(1), nullable=False, server_default=text("0"),
                      comment='Использовать для отправки электронной почты: 0-нет, 1-да')
    default_format = Column(String(16), comment='Выбираемый по умолчанию формат')

    counter = relationship('RbCounter')
    createPerson = relationship('Person', primaryjoin='RbPrintTemplate.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbPrintTemplate.modifyPerson_id == Person.id')

    @property
    def render_type(self):
        return 1

    @render_type.setter
    def render_type(self, value):
        if isinstance(value, dict):
            self.render = value.get('id')
        else:
            self.render = value

    def get_formats(self):
        return ['html']

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'render_type': 1,
            'formats': self.get_formats(),
            'default_format': self.default_format
        }


class RbTariffCategory(Base):
    __tablename__ = 'rbTariffCategory'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(16), nullable=False, comment='???')
    name = Column(String(64), nullable=False, comment='????????????')
    federalCode = Column(String(16), nullable=False, comment='??????????? ???')

    createPerson = relationship('Person', primaryjoin='RbTariffCategory.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbTariffCategory.modifyPerson_id == Person.id')


class RbUserProfile(Base):
    __tablename__ = 'rbUserProfile'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(16), nullable=False, comment='???')
    name = Column(String(128), nullable=False, comment='????????????')

    createPerson = relationship('Person', primaryjoin='RbUserProfile.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbUserProfile.modifyPerson_id == Person.id')


class RbBloodType(Base):
    __tablename__ = 'rbBloodType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='???? ???????? ??????')
    createPerson_id = Column(ForeignKey('Person.id'), comment='????? ?????? (??????? id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='???? ????????? ??????')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='????? ????????? ?????? {Person}')
    code = Column(String(32), nullable=False, comment='??? ?????? ?????')
    name = Column(String(64), nullable=False, comment='???????? ?????? ?????')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.3')

    createPerson = relationship('Person', primaryjoin='RbBloodType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbBloodType.modifyPerson_id == Person.id')


class RbNetTFOMS(Base):
    __tablename__ = 'rbNetTFOMS'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(32), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbNetTFOMS.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbNetTFOMS.modifyPerson_id == Person.id')


class Client(Base):
    __tablename__ = 'Client'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    # attendingPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL', onupdate='CASCADE'))
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    lastName = Column(String(30), nullable=False, comment='Фамилия')
    firstName = Column(String(30), nullable=False, comment='Имя')
    patrName = Column(String(30), nullable=False, comment='Отчество')
    birthDate = Column(Date, nullable=False, comment='Дата рождения')
    birthTime = Column(Time, nullable=False, comment='Время рождения')
    sex = Column(TINYINT(4), nullable=False, comment='Пол (0-неопределено, 1-М, 2-Ж)')
    SNILS = Column(CHAR(11), nullable=False, comment='СНИЛС')
    bloodType_id = Column(ForeignKey('rbBloodType.id', ondelete='SET NULL'), comment='Группа крови{rbBloodType}')
    bloodDate = Column(Date, comment='Дата установления группы крови')
    bloodNotes = Column(TINYTEXT, nullable=False, comment='Примечания к группе крови')
    growth = Column(String(16), nullable=False, comment='Рост при рождении')
    weight = Column(String(16), nullable=False, comment='Вес при рождении')
    embryonalPeriodWeek = Column(String(16), nullable=False,
                                 comment='Неделя эмбрионального периода(в которую рожден пациент)')
    birthPlace = Column(String(120), nullable=False, server_default=text("''"), comment='Место рождения')
    # chronicalMKB = Column(String(8), nullable=False, comment='Код A   хронического диагноза по МКБ')
    # diagNames = Column(String(64), nullable=False, comment='Коды диагнозов')
    # chartBeginDate = Column(Date, comment='Р”Р°С‚Р° РЅР°С‡Р°Р»Р° РІРµРґРµРЅРёСЏ РєР°СЂС‚С‹')
    # rbInfoSource_id = Column(ForeignKey('rbInfoSource.id', ondelete='SET NULL'), comment='Источник информации {rbInfoSource}')
    notes = Column(TINYTEXT, nullable=False, comment='Примечания')
    IIN = Column(String(15), comment='ИИН')
    isConfirmSendingData = Column(TINYINT(4), comment='Флаг отвечающий за согласие на передачу данных (i3093)')
    isUnconscious = Column(TINYINT(1), server_default=text("0"), comment='Флаг поступившего без сознания')
    mpi = Column(String(15), comment='МПИ')
    # filial = Column(INTEGER(10), comment='rbFilials.id Филиал, в котором было установлено значение Client.filial. NULL для всех новых клиентов после обновления, -1 для всех до обновления')
    # dataTransferConfirmationDate = Column(Date, comment='Дата согласия на передачу данных')
    # SNILSMissing_id = Column(INTEGER(11), comment='причина отсутсвия СНИЛС {rbSNILSMissingReason}')
    # patients_id = Column(INTEGER(11))

    # attendingPerson = relationship('Person', primaryjoin='Client.attendingPerson_id == Person.id')
    bloodType = relationship('RbBloodType')
    createPerson = relationship('Person', primaryjoin='Client.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='Client.modifyPerson_id == Person.id')
    # rbInfoSource = relationship('RbInfoSource')


class ClientIdentification(Base):
    __tablename__ = 'ClientIdentification'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id'), nullable=False, comment='Идентифицируемое лицо {Client}')
    accountingSystem_id = Column(ForeignKey('rbAccountingSystem.id'), nullable=False,
                                 comment='Внешняя учётная система {rbAccountingSystem}')
    identifier = Column(String(36))
    checkDate = Column(Date, comment='Дата подтверждения')

    accountingSystem = relationship('RbAccountingSystem')
    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientIdentification.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientIdentification.modifyPerson_id == Person.id')


class DeferredQueue(Base):
    __tablename__ = 'DeferredQueue'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(String(11), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    client_id = Column(ForeignKey('Client.id'), nullable=False, comment='Пациент {Client}')
    orgStructure_id = Column(ForeignKey('OrgStructure.id'), comment='Подразделение ЛПУ {orgStructure}')
    speciality_id = Column(ForeignKey('rbSpeciality.id'), nullable=False,
                           comment='Интересующая специальность {rbSpeciality}')
    person_id = Column(INTEGER(11), comment='Врач {Person} (если есть)')
    maxDate = Column(DateTime, comment='Дата, до которой интересует запись')
    status_id = Column(ForeignKey('rbDeferredQueueStatus.id'), nullable=False,
                       comment='Состояние записи {rbDeferredQueueStatus}')
    action_id = Column(ForeignKey('Action.id'), comment='Если status=2 - id номерка')
    comment = Column(Text, comment='Комментарий')
    contact = Column(String(128), comment='Номер телефона для связи')
    netrica_Code = Column(String(128), comment='Идентификатор записи в нетрике')

    action = relationship('Action')
    client = relationship('Client')
    orgStructure = relationship('OrgStructure')
    speciality = relationship('RbSpeciality')
    status = relationship('RbDeferredQueueStatu')


class Diagnosis(Base):
    __tablename__ = 'Diagnosis'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(INTEGER(11), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(INTEGER(11), nullable=False, comment='Пациент {Client}')
    diagnosisType_id = Column(ForeignKey('rbDiagnosisType.id'), nullable=False,
                              comment='Тип диагноза {rbDiagnosisType}')
    character_id = Column(ForeignKey('rbDiseaseCharacter.id'), comment='Характер заболевания {rbDiseaseCharacter}')
    MKB = Column(String(8), nullable=False, comment='Код по МКБ X (с пятым знаком)')
    MKBEx = Column(String(8), nullable=False, comment='Вторая секция кода по МКБ X (с пятым знаком)')
    morphologyMKB = Column(String(16), nullable=False, comment='Морфология диагноза МКБ')
    TNMS = Column(String(64), nullable=False, server_default=text("''"), comment='TNM + S')
    dispanser_id = Column(INTEGER(11), comment='Признак Д.Н. на дату конца периода {rbDispanser}')
    traumaType_id = Column(INTEGER(11), comment='тип травмы {rbTraumaType}')
    setDate = Column(Date,
                     comment='Для хрон.: дата выявления (если выявлено впервые) или NULL, для острого: дата начала')
    endDate = Column(Date, nullable=False,
                     comment='Для хрон.: дата последнего обращения , для острого: дата окончания или посл. обращения')
    mod_id = Column(INTEGER(11),
                    comment='ID уточнённого диагноза (тек. является исправленным и не учитывается в статистике) {Diagnosis}')
    person_id = Column(INTEGER(11), comment='Врач {Person}')
    tempEventId = Column(INTEGER(11))
    note = Column(Text)

    character = relationship('RbDiseaseCharacter')
    diagnosisType = relationship('RbDiagnosisType')


class TempInvalid(Base):
    __tablename__ = 'TempInvalid'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    type = Column(TINYINT(2), nullable=False, server_default=text("0"),
                  comment='Тип 0-ВУТ, 1-инвалидность, 2-ограничение жизнедеятельности')
    doctype = Column(TINYINT(4), nullable=False, comment='0-листок нетрудоспособности, 1-справка')
    doctype_id = Column(INTEGER(11), comment='Тип документа {rbTempInvalidDocument}')
    serial = Column(String(8), nullable=False, comment='Серия документа')
    number = Column(String(16), nullable=False, comment='Номер документа')
    client_id = Column(ForeignKey('Client.id'), nullable=False, comment='Пациент {Client}')
    tempInvalidReason_id = Column(ForeignKey('rbTempInvalidReason.id'),
                                  comment='Причина нетрудоспособности {rbTempInvalidReason}')
    begDate = Column(Date, nullable=False, comment='Дата начала временной утраты (мин. из периодов)')
    endDate = Column(Date, nullable=False, comment='Дата окончания временной утраты (макс. из периодов)')
    person_id = Column(ForeignKey('Person.id'), comment='Врач последего периода {Person}')
    diagnosis_id = Column(ForeignKey('Diagnosis.id'), comment='Диагноз последего периода {Diagnosis}')
    sex = Column(TINYINT(1), nullable=False, comment='Пол (1-М, 2-Ж)')
    age = Column(TINYINT(3), nullable=False, comment='Возраст')
    notes = Column(TINYTEXT, nullable=False, comment='Примечания')
    duration = Column(INTEGER(4), nullable=False, comment='Продолжительность в днях')
    closed = Column(TINYINT(1), nullable=False, comment='0-Открыт, 1-Закрыт, 2-Продлён, 3-Передан')
    prev_id = Column(INTEGER(11), comment='Предыдущий документ {TempInvalid}')
    insuranceOfficeMark = Column(INTEGER(11), nullable=False, server_default=text("0"),
                                 comment='Отметка страхового стола')
    caseBegDate = Column(Date, nullable=False, comment='Дата начала нетрудоспособности')
    tempInvalidExtraReason_id = Column(ForeignKey('rbTempInvalidExtraReason.id'),
                                       comment='Доп.причина нетрудоспособности{rbTempInvalidExtraReason}')
    busyness = Column(TINYINT(4), nullable=False, server_default=text("0"),
                      comment='Занятость:1- основное,2-совместитель,3-на учете')
    placeWork = Column(String(64), comment='Место работы')
    employmentService = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='Состоит ли на учёте в государственной службе занятости. 0 - не состоит, 1 - состоит')
    mainNumber = Column(String(16), comment='Номер основного листка')
    state = Column(INTEGER(11), server_default=text("0"),
                   comment='0 - новый, создан, с ним ничего не делали, 1 - подписан врачем, 2 - подписан ВК, 3 - подписан МО, 4 - отправлен в ФСС, 5 - анулирован')
    signedMessage = Column(Text, comment='Подписанное сообщение')
    is_ELN = Column(TINYINT(1), server_default=text("0"),
                    comment='Тип больничного листа: 0 - бумажный, 1 - электронный')
    ln_hash = Column(String(32), comment='Хэш данных листа нетрудоспособности')
    firstRelation = Column(String(64))
    secondRelation = Column(INTEGER(11), comment='Второе отношение по уходу {ClientRelation}')
    issueDate = Column(Date, comment='Дата выдачи листа')
    pregnancyTwelveWeeks = Column(TINYINT(1),
                                  comment='Отметка "Поставлена на учет в срок до 12 недель", в XML <PREGN12W_FLAG>')
    isDuplicate = Column(TINYINT(1), server_default=text("0"), comment='Отметка о дубликате, в XML <DUPLICATE_FLAG>')
    sanatoriumOGRN = Column(Text, comment='ОГРН санатория')
    regDateInMSE = Column(Date, comment='Дата регистрации документов в МСЭ')
    prolongFlag = Column(TINYINT(1), server_default=text("0"), comment='Флаг продления (1 - был продлён, 0 - не был)')
    prev_ln = Column(String(12), comment='Номер предыдущего ЛН')
    parent_id = Column(INTEGER(11), comment='Родительский лист')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='TempInvalid.createPerson_id == Person.id')
    diagnosis = relationship('Diagnosis')
    modifyPerson = relationship('Person', primaryjoin='TempInvalid.modifyPerson_id == Person.id')
    person = relationship('Person', primaryjoin='TempInvalid.person_id == Person.id')
    tempInvalidExtraReason = relationship('RbTempInvalidExtraReason')
    tempInvalidReason = relationship('RbTempInvalidReason')


class RbSocStatusClass(Base):
    __tablename__ = 'rbSocStatusClass'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    group_id = Column(ForeignKey('rbSocStatusClass.id', ondelete='SET NULL'), comment='Группировка {rbSocStatusClass}')
    code = Column(String(8), nullable=False, comment='Код')
    flatCode = Column(String(32), nullable=False,
                      comment='Код для однозначной идентификации класса социального статуса.')
    name = Column(String(64), nullable=False, comment='Наименование')
    tightControl = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Жёсткий контроль')
    isShowInClientInfo = Column(TINYINT(4), nullable=False, server_default=text("1"))
    autoCloseDate = Column(TINYINT(4), server_default=text("0"),
                           comment='Закрывать старую запись соц.статуса данного класса "вчерашней датой". 1 - закрывать, 0 - не закрывать.')
    softControl = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Мягкий контроль (i3683)')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.7')

    createPerson = relationship('Person', primaryjoin='RbSocStatusClass.createPerson_id == Person.id')
    group = relationship('RbSocStatusClass', remote_side=[id])
    modifyPerson = relationship('Person', primaryjoin='RbSocStatusClass.modifyPerson_id == Person.id')


class RbSocStatusClassTypeAssoc(Base):
    __tablename__ = 'rbSocStatusClassTypeAssoc'

    id = Column(INTEGER(11), primary_key=True)
    class_id = Column(ForeignKey('rbSocStatusClass.id', ondelete='CASCADE'), nullable=False,
                      comment='Ссылка на класс {rbSocStatusClass}')
    type_id = Column(ForeignKey('rbSocStatusType.id', ondelete='CASCADE'), nullable=False,
                     comment='Ссылка на тип {rbSocStatusType}')
    isDefault = Column(TINYINT(1), nullable=False, server_default=text("0"),
                       comment='Подставлять по умолчанию, если включен жесткий контроль')

    _class = relationship('RbSocStatusClass')
    type = relationship('RbSocStatusType')


class RbSocStatusType(Base):
    __tablename__ = 'rbSocStatusType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(250), nullable=False, comment='Наименование')
    socCode = Column(String(8), nullable=False, comment='код для социальной карты')
    regionalCode = Column(String(8), nullable=False, comment='Региональный код')
    documentType_id = Column(ForeignKey('rbDocumentType.id'), comment='Тип документа{rbDocumentType}')
    netrica_Code = Column(String(64), comment='Идентификатор МО в справочнике Нетрики')

    createPerson = relationship('Person', primaryjoin='RbSocStatusType.createPerson_id == Person.id')
    documentType = relationship('RbDocumentType')
    modifyPerson = relationship('Person', primaryjoin='RbSocStatusType.modifyPerson_id == Person.id')


class RbDeferredQueueStatu(Base):
    __tablename__ = 'rbDeferredQueueStatus'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    code = Column(String(8), nullable=False, comment='Код')
    flatCode = Column(String(32), nullable=False, comment='Код для автоматической обработки')
    name = Column(String(64), nullable=False, comment='Название')
    isSelectable = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Разрешается выбор в ЖОС')
    federalCode = Column(String(128),
                         comment='Используем значения из Нетрики:1-заявка активна;2-по заявке совершена запись на прием;3-заявка отменена')

    createPerson = relationship('Person', primaryjoin='RbDeferredQueueStatu.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbDeferredQueueStatu.modifyPerson_id == Person.id')


class RbDocumentType(Base):
    __tablename__ = 'rbDocumentType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    regionalCode = Column(String(16), nullable=False, comment='Региональный код')
    name = Column(String(64), nullable=False, comment='Наименование')
    group_id = Column(ForeignKey('rbDocumentTypeGroup.id'), nullable=False,
                      comment='Группа документов {rbDocumentTypeGroup}')
    serial_format = Column(INTEGER(11), nullable=False, comment='код формата серии')
    number_format = Column(INTEGER(11), nullable=False, comment='код формата номера')
    federalCode = Column(String(16), nullable=False, comment='Федеральный код')
    socCode = Column(String(8), nullable=False, comment='код для социальной карты')
    usedIndex = Column(Float(asdecimal=False), nullable=False, server_default=text("0"),
                       comment='Индекс частоты использования')
    isDefault = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Тип документа по умолчанию')
    isForeigner = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Признак иностранца')
    netrica_Code = Column(String(255))
    EGIZ_code = Column(INTEGER(11))
    autoCloseDate = Column(TINYINT(4), server_default=text("0"),
                           comment='Закрывать старую запись данного типа "вчерашней датой". 1 - закрывать, 0 - не закрывать.')

    createPerson = relationship('Person', primaryjoin='RbDocumentType.createPerson_id == Person.id')
    group = relationship('RbDocumentTypeGroup')
    modifyPerson = relationship('Person', primaryjoin='RbDocumentType.modifyPerson_id == Person.id')


class RbDocumentTypeGroup(Base):
    __tablename__ = 'rbDocumentTypeGroup'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbDocumentTypeGroup.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbDocumentTypeGroup.modifyPerson_id == Person.id')


class ClientAddress(Base):
    __tablename__ = 'ClientAddress'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False, comment='Лицо {Client}')
    type = Column(TINYINT(4), nullable=False, comment='0-регистрации, 1-проживания')
    address_id = Column(ForeignKey('Address.id'), comment='Адрес {Address}')
    freeInput = Column(String(200), nullable=False)
    district_id = Column(ForeignKey('rbDistrict.id', ondelete='SET NULL', onupdate='CASCADE'), comment='Р\xa0Р°Р№РѕРЅ')
    isVillager = Column(TINYINT(1), nullable=False, comment='Житель деревни')

    address = relationship('Address')
    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientAddress.createPerson_id == Person.id')
    district = relationship('RbDistrict')
    modifyPerson = relationship('Person', primaryjoin='ClientAddress.modifyPerson_id == Person.id')


class AddressHouse(Base):
    __tablename__ = 'AddressHouse'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    KLADRCode = Column(String(13), nullable=False, comment='код населённого пункта по КЛАДР')
    KLADRStreetCode = Column(String(17), nullable=False, comment='Код улицы по кладр')
    number = Column(String(8), nullable=False, comment='Номер дома')
    corpus = Column(String(8), nullable=False, comment='Корпус')
    litera = Column(String(8), comment='Литера')

    createPerson = relationship('Person', primaryjoin='AddressHouse.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='AddressHouse.modifyPerson_id == Person.id')

class ExcelExport(Base):
    __tablename__ = 'ExcelExport'

    id = Column(INTEGER(11), primary_key=True)
    path = Column(String(1024))
    period_day = Column(TINYINT(1))
    month = Column(TINYINT(2))
    name = Column(String(1024))

class Address(Base):
    __tablename__ = 'Address'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    house_id = Column(ForeignKey('AddressHouse.id'), nullable=False, comment='Дом {AddressHouse}')
    flat = Column(String(6), nullable=False, comment='Квартира')
    regBegDate = Column(Date, comment='Дата начала временной регистрации')
    regEndDate = Column(Date, comment='Дата окончания временной регистрации')

    createPerson = relationship('Person', primaryjoin='Address.createPerson_id == Person.id')
    house = relationship('AddressHouse')
    modifyPerson = relationship('Person', primaryjoin='Address.modifyPerson_id == Person.id')


class ClientAttach(Base):
    __tablename__ = 'ClientAttach'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False,
                       comment='Прикреплённое лицо {Client}')
    attachType_id = Column(ForeignKey('rbAttachType.id'), nullable=False, comment='Тип прикрепления {rbAttachType}')
    LPU_id = Column(INTEGER(11), nullable=False, comment='ЛПУ прикрепления {Organisation}')
    orgStructure_id = Column(ForeignKey('OrgStructure.id', ondelete='SET NULL'),
                             comment='Подразделение прикрепления {OrgStructure}')
    begDate = Column(Date, nullable=False, comment='Дата прикрепления')
    endDate = Column(Date, comment='Дата окончания прикрепления')
    document_id = Column(ForeignKey('ClientDocument.id'),
                         comment='Документ-основание для прикрепления {ClientDocument}')
    detachment_id = Column(ForeignKey('rbDetachmentReason.id', ondelete='SET NULL', onupdate='CASCADE'))
    sentToTFOMS = Column(TINYINT(1), nullable=False, comment='Признак корректного принятия записи в ТФОМС')
    errorCode = Column(String(256), comment='Описание ошибки')
    reason = Column(TINYINT(4), server_default=text("0"),
                    comment='Признак прикрепления (0-по заявлению, 1-по переезду, 4-смена участка)')

    attachType = relationship('RbAttachType')
    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientAttach.createPerson_id == Person.id')
    detachment = relationship('RbDetachmentReason')
    document = relationship('ClientDocument')
    modifyPerson = relationship('Person', primaryjoin='ClientAttach.modifyPerson_id == Person.id')
    orgStructure = relationship('OrgStructure')


class ClientContact(Base):
    __tablename__ = 'ClientContact'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id'), nullable=False, comment='Прикреплённое лицо {Client}')
    contactType_id = Column(ForeignKey('rbContactType.id'), nullable=False,
                            comment='Тип контакта телефон/e-mail {rbContactType}')
    isPrimary = Column(TINYINT(1), nullable=False, server_default=text("0"),
                       comment='Признак основного контакта (0 - не основной контакт, 1 - основной контакт)')
    contact = Column(String(32), nullable=False, comment='Контакт')
    notes = Column(String(64), nullable=False, comment='Контакт')
    # agreement = Column(String(100), server_default=text("''"))

    client = relationship('Client')
    contactType = relationship('RbContactType')
    createPerson = relationship('Person', primaryjoin='ClientContact.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientContact.modifyPerson_id == Person.id')


class ClientPolicy(Base):
    __tablename__ = 'ClientPolicy'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False,
                       comment='Лицо, на которое выдан полис {Client}')
    insurer_id = Column(INTEGER(11), comment='Страховая организация {Organisation}')
    policyType_id = Column(ForeignKey('rbPolicyType.id'), comment='Тип полиса {rbPolicyType}')
    policyKind_id = Column(ForeignKey('rbPolicyKind.id', ondelete='SET NULL', onupdate='CASCADE'),
                           comment='Вид полиса (старый, временный, новый) {rbPolicyType}')
    serial = Column(String(16), nullable=False, comment='Серия полиса')
    number = Column(String(35), nullable=False, comment='Номер полиса')
    begDate = Column(Date, nullable=False, comment='Дата выдачи полиса')
    endDate = Column(Date, comment='Дата окончания действия полиса')
    dischargeDate = Column(Date, comment='Дата погашения полиса')
    name = Column(String(64), nullable=False, server_default=text("''"), comment='Название')
    note = Column(String(200), nullable=False, server_default=text("''"), comment='Примечание')
    insuranceArea = Column(String(13), nullable=False,
                           comment='Территория страхования (более конкретная, нежели территория страхователя)')
    isSearchPolicy = Column(TINYINT(1), nullable=False, server_default=text("0"),
                            comment='Использование веб-сервиса (0-не использовался; 1-полис не найден; 2-полис найден)')
    franchisePercent = Column(Float, server_default=text("0"), comment='Процент франшизы владельца полиса (i3085)')
    # enp = Column(String(20), comment='Единый номер полиса')
    # discharge_id = Column(ForeignKey('rbPolicyDischargeReason.id'), comment='Причина аннулирования')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientPolicy.createPerson_id == Person.id')
    # discharge = relationship('RbPolicyDischargeReason')
    modifyPerson = relationship('Person', primaryjoin='ClientPolicy.modifyPerson_id == Person.id')
    policyKind = relationship('RbPolicyKind')
    policyType = relationship('RbPolicyType')


class RbPolicyDischargeReason(Base):
    __tablename__ = 'rbPolicyDischargeReason'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbPolicyDischargeReason.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbPolicyDischargeReason.modifyPerson_id == Person.id')


class ClientRelation(Base):
    __tablename__ = 'ClientRelation'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), comment='Номер клиента {Client}')
    relativeType_id = Column(ForeignKey('rbRelationType.id'), ForeignKey('rbRelationType.id'),
                             comment='Тип связи {rbRelationType}')
    relative_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), comment='Id связанного с пациентом {Client}')
    freeInput = Column(String(80),
                       comment='Данные о связанном с пациентом лицом. Используется, если id связанного лица = -1.')

    client = relationship('Client', primaryjoin='ClientRelation.client_id == Client.id')
    createPerson = relationship('Person', primaryjoin='ClientRelation.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientRelation.modifyPerson_id == Person.id')
    relativeType = relationship('RbRelationType', primaryjoin='ClientRelation.relativeType_id == RbRelationType.id')
    relativeType1 = relationship('RbRelationType', primaryjoin='ClientRelation.relativeType_id == RbRelationType.id')
    relative = relationship('Client', primaryjoin='ClientRelation.relative_id == Client.id')


class ClientSocStatus(Base):
    __tablename__ = 'ClientSocStatus'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id'), nullable=False, comment='Прикреплённое лицо {Client}')
    socStatusClass_id = Column(INTEGER(11), comment='{rbSocStatusClass}')
    socStatusType_id = Column(ForeignKey('rbSocStatusType.id'), nullable=False, comment='{rbSocStatusType}')
    begDate = Column(Date, nullable=False, comment='Дата начала действия записи')
    endDate = Column(Date, comment='Дата окончания действия записи')
    document_id = Column(INTEGER(11), comment='Подтверджающий документ {ClientDocument}')
    notes = Column(TINYTEXT, comment='Примечание')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientSocStatus.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientSocStatus.modifyPerson_id == Person.id')
    socStatusType = relationship('RbSocStatusType')


class ClientDocument(Base):
    __tablename__ = 'ClientDocument'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False,
                       comment='Лицо, на которое выдан документ {Client}')
    documentType_id = Column(ForeignKey('rbDocumentType.id'), nullable=False, comment='Тип документа {rbDocumentType}')
    serial = Column(String(8), nullable=False, comment='Серия документа')
    number = Column(String(16), nullable=False, comment='Номер документа')
    date = Column(DateTime, nullable=False, comment='Дата начала действия документа')
    origin = Column(String(128), nullable=False, server_default=text("''"), comment='Организация, выдавшая документ')
    endDate = Column(DateTime, comment='Дата окончания действия документа')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientDocument.createPerson_id == Person.id')
    documentType = relationship('RbDocumentType', primaryjoin='ClientDocument.documentType_id == RbDocumentType.id',
                                lazy=True)
    modifyPerson = relationship('Person', primaryjoin='ClientDocument.modifyPerson_id == Person.id')


class ClientDisability(Base):
    __tablename__ = 'ClientDisability'

    id = Column(INTEGER(11), primary_key=True)
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                       comment='Идентификатор пациента {Client}')
    setDate = Column(Date, nullable=False, comment='Дата установки инвалидности')
    groupNumber = Column(INTEGER(11), comment='Группа инвалидности')
    recertificationDate = Column(Date, comment='Дата очередного переосвидетельствования.\\n')
    work_id = Column(ForeignKey('ClientWork.id', ondelete='SET NULL', onupdate='SET NULL'), comment='Место работа')
    degree = Column(INTEGER(11), comment='Степень утраты трудоспособности')
    note = Column(VARCHAR(256), nullable=False, comment='Примечание')
    isPrimary = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='Признак первичности')
    isSomatic = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Cоматическая инвалидность')
    isStationary = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Стационар')
    isTermless = Column(TINYINT(1), server_default=text("0"), comment='Бессрочно')

    client = relationship('Client')
    work = relationship('ClientWork')


class ClientDispanserization(Base):
    __tablename__ = 'ClientDispanserization'

    id = Column(INTEGER(11), primary_key=True)
    create_datetime = Column(DateTime, nullable=False, comment='Дата и время создания записи')
    client_id = Column(INTEGER(11), nullable=False, comment='Ид клиента')
    code = Column(String(8), nullable=False, comment='Код вида оказания помощи')
    date_begin = Column(DateTime, nullable=False, comment='Дата начала диспансеризации/профосмотра')
    date_end = Column(DateTime, nullable=False, comment='Дата окончания диспансеризации/профосмотра')
    codeMO = Column(String(8), nullable=False, comment='Код СМО')


class ClientWork(Base):
    __tablename__ = 'ClientWork'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(INTEGER(11), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False,
                       comment='Прикреплённое лицо {Client}')
    org_id = Column(INTEGER(11), comment='Место работы {Organisation}')
    freeInput = Column(String(128), nullable=False, comment='Свободный ввод для имени организации')
    post = Column(String(64), nullable=False, comment='Должность')
    stage = Column(TINYINT(3), nullable=False, comment='Стаж')
    OKVED = Column(String(10), nullable=False, comment='ОКВЭД')
    note = Column(String(100), nullable=False, server_default=text("''"), comment='Примечание')
    workPost = Column(INTEGER(11), comment='Должность {rbProfessionsPositions}')
    workType = Column(INTEGER(11), comment='Тип занятости {rbEmploymentType}')

    client = relationship('Client')


class ClientWorkHurt(Base):
    __tablename__ = 'ClientWork_Hurt'

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(ForeignKey('ClientWork.id', ondelete='CASCADE'), nullable=False,
                       comment='Главная запись {ClientWork}')
    hurtType_id = Column(ForeignKey('rbHurtType.id'), nullable=False, comment='Тип вредности {rbHurtType}')
    stage = Column(TINYINT(3), nullable=False, comment='Стаж')

    hurtType = relationship('RbHurtType')
    master = relationship('ClientWork')


class ClientWorkHurtFactor(Base):
    __tablename__ = 'ClientWork_Hurt_Factor'

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(ForeignKey('ClientWork.id', ondelete='CASCADE'), comment='"Главная" запись {ClientWork}')
    factorType_id = Column(ForeignKey('rbHurtFactorType.id'), nullable=False,
                           comment='Фактор вредности {rbHurtFactorType}')

    factorType = relationship('RbHurtFactorType')
    master = relationship('ClientWork')


class User(Base):
    __tablename__ = 'User'

    id = Column(INTEGER(11), primary_key=True)
    username = Column(String(128), nullable=False, comment='Логин')
    password = Column(String(64), nullable=False, comment='Хеш пароля')
    email = Column(String(128), comment='Емейл, использующийся для сброса пароля')
    createDatetime = Column(DateTime)


class UserWithName(User):
    lastName = Column(String(30), nullable=False, comment='Фамилия')
    firstName = Column(String(30), nullable=False, comment='Имя')
    patrName = Column(String(30), nullable=False, comment='Отчество')


class UserPerson(Base):
    __tablename__ = 'User_Person'

    id = Column(INTEGER(11), primary_key=True)
    person_id = Column(INTEGER(11), comment='{Person}')
    user_id = Column(INTEGER(11), comment='{User}')
    isPreferable = Column(TINYINT(4), nullable=False, server_default=text("0"),
                          comment='Поле для определения учетки по умолчанию')


class EventLittleStranger(Base):
    __tablename__ = 'Event_LittleStranger'

    id = Column(INTEGER(11), primary_key=True)
    birthDate = Column(Date, comment='Дата рождения')
    sex = Column(TINYINT(4), comment='Пол (0-неопределено, 1-М, 2-Ж)')
    currentNumber = Column(TINYINT(2), nullable=False, server_default=text("1"), comment='Номер ребенка по счету')
    multipleBirths = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Признак многоплодных родов')
    birthWeight = Column(DECIMAL(6, 2), nullable=False)


class OrgStructurePrinter(Base):
    __tablename__ = 'OrgStructure_Printers'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(INTEGER(11), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    master_id = Column(ForeignKey('OrgStructure.id', ondelete='CASCADE'), nullable=False,
                       comment='Подразделение {OrgStructure}')
    name = Column(Text)

    master = relationship('OrgStructure')


class QuotaType(Base):
    __tablename__ = 'QuotaType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(INTEGER(11), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    _class = Column('class', TINYINT(1), nullable=False,
                    comment='0 - ВТМП (ВМП)\\n1 - СМП\\n2 - Родовой сертификат\\n3 - Платные\\n4 - ОМС\\n5 - ОМС из ВМП\\n6 - ВМП сверх базового')
    group_code = Column(String(16), comment='Поле для группировки квот {QuotaType}')
    code = Column(String(16), nullable=False, comment='Код')
    name = Column(String(255), nullable=False, comment='Наименование квоты')
    isObsolete = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Устаревший')


class Bank(Base):
    __tablename__ = 'Bank'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    BIK = Column(String(10), nullable=False, comment='БИК (МФО)')
    name = Column(String(100), nullable=False, comment='Наименование')
    branchName = Column(String(100), nullable=False, comment='Наименование филиала')
    corrAccount = Column(String(20), nullable=False, comment='Кор.счет')
    subAccount = Column(String(20), nullable=False, comment='Суб.счет')

    createPerson = relationship('Person', primaryjoin='Bank.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='Bank.modifyPerson_id == Person.id')


class RbDiagnosisType(Base):
    __tablename__ = 'rbDiagnosisType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    replaceInDiagnosis = Column(String(8), nullable=False, comment='При записи в Diagnosis заменить на код')
    netrica_Code = Column(String(64), comment='Идентификатор МО в справочнике Нетрики')

    createPerson = relationship('Person', primaryjoin='RbDiagnosisType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbDiagnosisType.modifyPerson_id == Person.id')


class RbDiseaseCharacter(Base):
    __tablename__ = 'rbDiseaseCharacter'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    replaceInDiagnosis = Column(String(8), nullable=False, comment='При записи в Diagnosis заменить на код')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.8')
    EIScode = Column(String(64))

    createPerson = relationship('Person', primaryjoin='RbDiseaseCharacter.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbDiseaseCharacter.modifyPerson_id == Person.id')


class RbDetachmentReason(Base):
    __tablename__ = 'rbDetachmentReason'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    attachType_id = Column(ForeignKey('rbAttachType.id'),
                           comment='Тип открепления, для которого работает причина {rbAttachType}')

    attachType = relationship('RbAttachType')
    createPerson = relationship('Person', primaryjoin='RbDetachmentReason.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbDetachmentReason.modifyPerson_id == Person.id')


class RbTempInvalidExtraReason(Base):
    __tablename__ = 'rbTempInvalidExtraReason'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    type = Column(TINYINT(2), nullable=False, server_default=text("0"),
                  comment='Тип 0-ВУТ, 1-инвалидность, 2-ограничение жизнедеятельности')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(128), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbTempInvalidExtraReason.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbTempInvalidExtraReason.modifyPerson_id == Person.id')


class RbTempInvalidReason(Base):
    __tablename__ = 'rbTempInvalidReason'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    type = Column(TINYINT(2), nullable=False, server_default=text("0"),
                  comment='Тип 0-ВУТ, 1-инвалидность, 2-ограничение жизнедеятельности')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    requiredDiagnosis = Column(TINYINT(1), nullable=False, comment='В Б/Л требуется диагноз')
    grouping = Column(TINYINT(1), nullable=False, comment='0-заболевание, 1-уход, 2-беременность и роды')
    primary = Column(INTEGER(11), nullable=False, comment='максимальная длительность первичного периода ВУТ в днях')
    prolongate = Column(INTEGER(11), nullable=False, comment='максимальная длительность продления ВУТ в днях')
    restriction = Column(INTEGER(11), nullable=False, comment='ограничение периода ВУТ, после которого требуется КЭК')
    regionalCode = Column(String(3), nullable=False, comment='Региональный код')

    createPerson = relationship('Person', primaryjoin='RbTempInvalidReason.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbTempInvalidReason.modifyPerson_id == Person.id')


class RbTempInvalidDocument(Base):
    __tablename__ = 'rbTempInvalidDocument'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    type = Column(TINYINT(2), nullable=False, comment='Тип 0-ВУТ, 1-инвалидность, 2-ограничение жизнедеятельности')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(80), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbTempInvalidDocument.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbTempInvalidDocument.modifyPerson_id == Person.id')


class RbRelationType(Base):
    __tablename__ = 'rbRelationType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='код')
    leftName = Column(String(64), nullable=False, comment='Субъект отношения')
    rightName = Column(String(64), nullable=False, comment='Объект отношения')
    isDirectGenetic = Column(TINYINT(1), nullable=False, server_default=text("0"),
                             comment='Передача генетичекого материала ->')
    isBackwardGenetic = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='Передача генетичекого материала <-')
    isDirectRepresentative = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='Представительство ->')
    isBackwardRepresentative = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                      comment='Представительство <-')
    isDirectEpidemic = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Эпид.контакт ->')
    isBackwardEpidemic = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Эпид.контакт <-')
    isDirectDonation = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Донорство ->')
    isBackwardDonation = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Донорство <-')
    leftSex = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='0-неопределено, 1-М, 2-Ж')
    rightSex = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='0-неопределено, 1-М, 2-Ж')
    regionalCode = Column(String(64), nullable=False, comment='Региональный (инфис) код')
    regionalReverseCode = Column(String(64), nullable=False, comment='Региональный (инфис) код обратного отношения')
    netrica_Code = Column(String(65), comment='1.2.643.5.1.13.2.7.1.15')

    createPerson = relationship('Person', primaryjoin='RbRelationType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbRelationType.modifyPerson_id == Person.id')


class RbTest(Base):
    __tablename__ = 'rbTest'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    testGroup_id = Column(ForeignKey('rbTestGroup.id', ondelete='SET NULL'), comment='Группа теста {rbTestGroup}')
    code = Column(String(16), nullable=False, comment='Код')
    name = Column(String(128), nullable=False, comment='Наименование')
    position = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='Позиция')
    lis_id = Column(INTEGER(11), comment='Идентификатор теста в ЛИС')

    createPerson = relationship('Person', primaryjoin='RbTest.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbTest.modifyPerson_id == Person.id')
    testGroup = relationship('RbTestGroup')


class RbTestGroup(Base):
    __tablename__ = 'rbTestGroup'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(16), nullable=False, comment='Код')
    name = Column(String(32), nullable=False, comment='Наименование')
    group_id = Column(INTEGER(11), comment='Группа предок')

    createPerson = relationship('Person', primaryjoin='RbTestGroup.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbTestGroup.modifyPerson_id == Person.id')


class RbAccountExportFormat(Base):
    __tablename__ = 'rbAccountExportFormat'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    prog = Column(String(128), nullable=False, comment='Имя подпрограммы и при необходимости параметры')
    preferentArchiver = Column(String(128), nullable=False, comment='Предпочитаемый архиватор')
    emailRequired = Column(TINYINT(1), nullable=False, comment='требуется отправка по e-mail')
    emailTo = Column(String(64), nullable=False, comment='адрес эл.почты')
    subject = Column(String(128), nullable=False, comment='тема сообщения. используйте %(Name)s для подстановки')
    message = Column(Text, nullable=False, comment='шаблон сообщения, используйте %(Name)s для подстановки')

    createPerson = relationship('Person', primaryjoin='RbAccountExportFormat.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbAccountExportFormat.modifyPerson_id == Person.id')


class RbAccountingSystem(Base):
    __tablename__ = 'rbAccountingSystem'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    isEditable = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='Разрешать изменение в регистрационной карте пациента')
    showInClientInfo = Column(TINYINT(1), nullable=False, server_default=text("0"),
                              comment='Отображать в окне информации о пациенте')
    isUnique = Column(TINYINT(1), nullable=False, server_default=text("0"),
                      comment='Требуется ввод уникального значения')
    counter_id = Column(INTEGER(11), comment='\x7f\x7fИспользуемый счетчик {rbCounter}')
    autoIdentificator = Column(TINYINT(1), server_default=text("0"), comment='Автоматическое добавление идентификатора')

    createPerson = relationship('Person', primaryjoin='RbAccountingSystem.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbAccountingSystem.modifyPerson_id == Person.id')


class RbActionShedule(Base):
    __tablename__ = 'rbActionShedule'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(16), nullable=False, server_default=text("''"), comment='Код')
    name = Column(String(64), nullable=False, server_default=text("''"), comment='Наименование')
    period = Column(TINYINT(2), nullable=False, server_default=text("1"), comment='Период; ежедневно = 1')

    createPerson = relationship('Person', primaryjoin='RbActionShedule.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbActionShedule.modifyPerson_id == Person.id')


class RbAttachType(Base):
    __tablename__ = 'rbAttachType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    temporary = Column(TINYINT(1), nullable=False, comment='Временное прикрепление')
    outcome = Column(TINYINT(4), nullable=False, comment='Признак выбытия')
    finance_id = Column(ForeignKey('rbFinance.id'), nullable=False, comment='Тип финансирования {rbFinance}')
    grp = Column(TINYINT(2), nullable=False, server_default=text("0"),
                 comment='Группа, в рамках которой прикрепления взаимоисключающие. 0 - не задана.')

    createPerson = relationship('Person', primaryjoin='RbAttachType.createPerson_id == Person.id')
    finance = relationship('RbFinance')
    modifyPerson = relationship('Person', primaryjoin='RbAttachType.modifyPerson_id == Person.id')


class RbHighTechCureKind(Base):
    __tablename__ = 'rbHighTechCureKind'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(9), nullable=False, comment='Код')
    name = Column(String(400), nullable=False, comment='Название')
    regionalCode = Column(String(8), nullable=False, server_default=text("''"), comment='Региональный код')
    federalCode = Column(String(16), nullable=False, server_default=text("''"), comment='Федеральный код')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка об удалении')
    beginDate = Column(Date)
    endDate = Column(Date)

    createPerson = relationship('Person', primaryjoin='RbHighTechCureKind.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbHighTechCureKind.modifyPerson_id == Person.id')


class RbHurtFactorType(Base):
    __tablename__ = 'rbHurtFactorType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(16), nullable=False, comment='Код')
    name = Column(String(250), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbHurtFactorType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbHurtFactorType.modifyPerson_id == Person.id')


class RbHurtType(Base):
    __tablename__ = 'rbHurtType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(256), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbHurtType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbHurtType.modifyPerson_id == Person.id')


class RbPolicyKind(Base):
    __tablename__ = 'rbPolicyKind'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, server_default=text("''"), comment='Код')
    regionalCode = Column(String(8), nullable=False, server_default=text("''"), comment='Региональный код')
    federalCode = Column(String(8), nullable=False, server_default=text("''"), comment='Федеральный код')
    name = Column(String(64), nullable=False, server_default=text("''"), comment='Наименование')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.59')

    createPerson = relationship('Person', primaryjoin='RbPolicyKind.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbPolicyKind.modifyPerson_id == Person.id')


class RbHospitalBedProfile(Base):
    __tablename__ = 'rbHospitalBedProfile'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    regionalCode = Column(String(16), nullable=False, server_default=text("''"), comment='Региональный код')
    name = Column(String(512))
    service_id = Column(ForeignKey('rbService.id', ondelete='SET NULL'), comment='Базовый сервис ОМС {rbService}')
    medicalAidProfile_id = Column(ForeignKey('rbMedicalAidProfile.id', ondelete='SET NULL', onupdate='CASCADE'),
                                  comment='Профиль мед. помощи {rbMedicalAidProfile}')
    emsProfileCode = Column(String(32), nullable=False,
                            comment='Код профиля в бюро госпитализации (ems == emergency medical service)')
    usishCode = Column(String(64), nullable=False)
    eisCode = Column(String(15), comment='Идентификатор профиля койки (ID_B_PROF в экспорте ЕИС)')
    paidFlag = Column(TINYINT(1), server_default=text("0"), comment='Признак платной койки')
    netrica_Code = Column(String(65), comment='1.2.643.5.1.13.2.1.1.221')
    row_code = Column(String(10))

    createPerson = relationship('Person', primaryjoin='RbHospitalBedProfile.createPerson_id == Person.id')
    medicalAidProfile = relationship('RbMedicalAidProfile')
    modifyPerson = relationship('Person', primaryjoin='RbHospitalBedProfile.modifyPerson_id == Person.id')
    service = relationship('RbService')


class RbHospitalBedShedule(Base):
    __tablename__ = 'rbHospitalBedShedule'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbHospitalBedShedule.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbHospitalBedShedule.modifyPerson_id == Person.id')


class RbHospitalBedType(Base):
    __tablename__ = 'rbHospitalBedType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbHospitalBedType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbHospitalBedType.modifyPerson_id == Person.id')


class RbPolicyType(Base):
    __tablename__ = 'rbPolicyType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbPolicyType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbPolicyType.modifyPerson_id == Person.id')


class RbTissueType(Base):
    __tablename__ = 'rbTissueType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(64), nullable=False, comment='Код')
    name = Column(String(128), nullable=False, comment='Наименование')
    group_id = Column(ForeignKey('rbTissueType.id', ondelete='SET NULL'),
                      comment='Поле группирвки типа ткани {rbTissueType}')
    sex = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='0-Любой пол, 1-М, 2-Ж')
    counterManualInput = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='Ручной (в т.ч. со сканера) ввод идентификатора')
    counterResetType = Column(TINYINT(1), nullable=False, server_default=text("0"),
                              comment='Тип сброса счетчика 0-день, 1-неделя, 2-месяц, 3-полугодие, 4-год, 5-никогда')
    issueExternalIdLimit = Column(INTEGER(11), server_default=text("0"),
                                  comment='Ограничение количества символов для ввода')
    masterActionType_id = Column(INTEGER(11), comment='{ActionType} Главное действие для данного биоматериала')
    lis_id = Column(INTEGER(11), comment='Идентификатор биоматериала в ЛИС')

    createPerson = relationship('Person', primaryjoin='RbTissueType.createPerson_id == Person.id')
    group = relationship('RbTissueType', remote_side=[id])
    modifyPerson = relationship('Person', primaryjoin='RbTissueType.modifyPerson_id == Person.id')


class RbUnit(Base):
    __tablename__ = 'rbUnit'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(48), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    netrica_Code = Column(String(9))

    createPerson = relationship('Person', primaryjoin='RbUnit.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbUnit.modifyPerson_id == Person.id')


class ActionType(Base):
    __tablename__ = 'ActionType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    _class = Column('class', TINYINT(1), nullable=False,
                    comment='0-статус, 1-диагностика, 2-лечение, 3-прочие мероприятия')
    group_id = Column(ForeignKey('ActionType.id'), comment='Поле для группировки действия {ActionType}')
    code = Column(String(15), nullable=False, comment='Код')
    name = Column(String(1024), nullable=False, comment='Наименование действия')
    title = Column(String(255), nullable=False, comment='Наименование для печати')
    flatCode = Column(String(64), nullable=False,
                      comment='"Плоский" код. в противовес code должен быть уникальным, используется для отчётов, импортов и экспортов')
    sex = Column(TINYINT(4), nullable=False, comment='Применимо для указанного пола (0-любой, 1-М, 2-Ж)')
    age = Column(String(9), nullable=False,
                 comment='Применимо для указанного интервала возрастов пусто-нет ограничения, "{NNN{д|н|м|г}-{MMM{д|н|м|г}}" - с NNN дней/недель/месяцев/лет по MMM дней/недель/месяцев/лет; пустая нижняя или верхняя граница - нет ограничения снизу или сверху')
    office = Column(String(32), nullable=False, comment='Кабинет по умолчанию')
    showInForm = Column(TINYINT(1), nullable=False, comment='Разрешается выбор в формах ввода событий')
    genTimetable = Column(TINYINT(1), nullable=False, comment='Генерировать график (приём)')
    quotaType_id = Column(ForeignKey('QuotaType.id', ondelete='SET NULL'), comment='Вид квоты {QuotaType}')
    context = Column(String(64), nullable=False, comment='Контекст печати ')
    amount = Column(Float(asdecimal=True), nullable=False, server_default=text("1"), comment='Количество по умолчанию')
    amountEvaluation = Column(INTEGER(1), nullable=False, server_default=text("0"),
                              comment='0-Количество вводится непосредственно, 1-По числу визитов, 2-По длительности события, 3-По длительности события без выходных дней, 4-По длительности действия, 5-По длительности действия без выходных дней, 6-По заполненным свойствам действия')
    defaultStatus = Column(TINYINT(4), nullable=False, server_default=text("0"),
                           comment='Значение по умолчанию для статуса выполнения: 0-Начато, 1-Ожидание, 2-Закончено, 3-Отменено')
    defaultDirectionDate = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                  comment='Код значение по умолчанию для даты назначения действияия: 0-Не задано, 1-По дате начала события, 2-Текущая дата, 3-Синхронизация по дате выполнения, 4-Синхронизация по дате начала события')
    defaultPlannedEndDate = Column(TINYINT(1), nullable=False,
                                   comment='Планируемя дата выполнения (0=не определено, 1=След. день, 2=След. рабочий день, 3=Дата талона на Работу, 4=Дата начала + количество, 5=Дата начала + длительность)')
    defaultEndDate = Column(TINYINT(4), nullable=False, server_default=text("0"),
                            comment='Код значение по умолчанию для даты выполнения события: 0-Пусто, 1-Тек.дата, 2-Дата начала события, 3-Дата окончания события, 4-Синхронизация по дате начала события')
    defaultExecPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL'),
                                  comment='Предопределенный ответственный за действие в событии{Person}')
    defaultSetPerson_id = Column(ForeignKey('Person.id'),
                                 comment='Предопределенный назначивший действие врач в событии {Person}')
    defaultPersonInEvent = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                  comment='исполнитель в редакторе события: 0-Не определено, 1-Не заполняется, 2-Назначивший действие, 3-Ответственный за событие, 4-Пользователь')
    defaultPersonInEditor = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                   comment='исполнитель в отдельном редакторе: 0-Не определено, 1-Не заполняется, 2-Назначивший действие, 3-Ответственный за событие, 4-Пользователь')
    defaultMKB = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='Правило заполнения по умолчанию поля Action.`MKB` (0-не используется, 1-по диагнозу назначившего действие, 2-синхронизировать с заключительным, 3-синхронизировать с диагнозом назначившего действие)')
    defaultMorphology = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='Правило заполнения по умолчанию поля Action.`morphologyMKB` (0-не используется, 1-по диагнозу назначившего действие, 2-синхронизировать с заключительным, 3-синхронизировать с диагнозом назначившего действие)')
    isMorphologyRequired = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                  comment='0-Не контролировать, 1-Запполнять не обязательно(мягкий контроль), 2-нужно заполнить(жесткий контроль)')
    defaultOrg_id = Column(INTEGER(11), comment='Организация выполняющая действие по умолчанию {Organisation}')
    showTime = Column(TINYINT(1), nullable=False, server_default=text("0"),
                      comment='Показывать в интерфейсе не только дату, но и время назначения/начала/окончания')
    maxOccursInEvent = Column(INTEGER(11), nullable=False, server_default=text("0"),
                              comment='Ограничение регистрации действий по по количеству в событии')
    isMES = Column(INTEGER(11), comment='Является стандартом')
    nomenclativeService_id = Column(ForeignKey('rbService.id', ondelete='SET NULL'),
                                    comment='Номенклатурная услуга {rbService}')
    isPreferable = Column(TINYINT(1), nullable=False, server_default=text("1"),
                          comment='Является предпочитаемым (выполняемым?) в данном ЛПУ')
    prescribedType_id = Column(ForeignKey('ActionType.id', ondelete='SET NULL', onupdate='CASCADE'),
                               comment='Предписываемое действие {ActionType}')
    shedule_id = Column(ForeignKey('rbActionShedule.id', ondelete='SET NULL', onupdate='CASCADE'),
                        comment='График по умолчанию {rbActionShedule}')
    isRequiredCoordination = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='Требуется обязательное согласование')
    isNomenclatureExpense = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                   comment='Является тратой ЛСиИМН (Возможно списание ЛСиИМН)')
    hasAssistant = Column(TINYINT(1), nullable=False, server_default=text("0"),
                          comment='Ввод ассистента: 0 - не треб, 1 - не обяз, 2 - обяз')
    propertyAssignedVisible = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                     comment='Визуализация `назначено` в свойствах действия')
    propertyUnitVisible = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                 comment='Визуализация `ед.изм.` в свойствах действия')
    propertyNormVisible = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                 comment='Визуализация `норма` в свойствах действия')
    propertyEvaluationVisible = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                       comment='Визуализация `оценка` в свойствах действия')
    serviceType = Column(TINYINT(1), nullable=False, server_default=text("0"),
                         comment='Вид услуги: 0-Прочие, 1-первичный осмотр, 2-повторный осмотр, 3-процедура/манипуляция, 4-операция, 5-исследование, 6-лечение')
    actualAppointmentDuration = Column(SMALLINT(6), nullable=False, server_default=text("0"),
                                       comment='Актуальность при назначении')
    isSubstituteEndDateToEvent = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                        comment='Подстановка даты окончания дейтсвия в дату окончания события')
    isPrinted = Column(TINYINT(1), nullable=False, server_default=text("1"),
                       comment='Выводить на печать действие этого типа (проверяться должно в шаблоне печати: Action.isPrinted)')
    defaultMES = Column(TINYINT(4), nullable=False, server_default=text("0"),
                        comment='МЭС по умолчанию. 0 - Не используется; 1 - Стандарт из события; 2 - Пустой')
    frequencyCount = Column(INTEGER(11), nullable=False, server_default=text("0"),
                            comment='Допустимая частота повторного назначения услуги пациенту за определенный период. 0 - нет ограничений на количество повторов.')
    frequencyPeriod = Column(TINYINT(4), nullable=False, server_default=text("0"),
                             comment='Размер периода для контроля частоты назначений услуги. Если 0, то учитывается весь возможный диапазон.')
    frequencyPeriodType = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                 comment='Тип периода для контроля частоты повторного назначения: 0-нет, 1-неделя, 2-месяц, 3-квартал, 4-полугодие, 5-год')
    isStrictFrequency = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='0-мягкая проверка, 1-жесткая проверка')
    isFrequencyPeriodByCalendar = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                         comment='Использовать календарные периоды вместо абсолютных. То есть правило "раз в неделю" будет трактоваться как "раз в календарную неделю (с Пн по Вс), а не  "раз в 7 дней".')
    counter_id = Column(INTEGER(11), comment='счетчик')
    isCustomSum = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Возможен ручной ввод цены')
    recommendationExpirePeriod = Column(INTEGER(11), server_default=text("0"),
                                        comment='Срок актуальности направления в днях')
    recommendationControl = Column(TINYINT(1), server_default=text("0"), comment='Контроль назначившего')
    isExecRequiredForEventExec = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                        comment='Необходимо состояние не "начато" для закрытия обращения')
    isActiveGroup = Column(TINYINT(1), nullable=False, comment='Событие, которое заменяет параметры дочерних действий')
    lis_code = Column(String(32), comment='Код анализа в ЛИС')
    locked = Column(TINYINT(1), nullable=False, server_default=text("0"),
                    comment='Удаление разрешено только администратору и пользователям, имеющим соответствующее право')
    filledLock = Column(TINYINT(1), server_default=text("0"),
                        comment='Запрещать удаление если заполнено хотя бы одно свойство')
    defaultBeginDate = Column(TINYINT(4), nullable=False, server_default=text("0"),
                              comment='Дата начала действия по умолчанию: 0-Не задано, 1-По дате начала события, 2-Текущая дата, 3-Синхронизация по дате выполнения, 4-Синхронизация по дате начала события')
    refferalType_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Тип направления')
    filterPosts = Column(TINYINT(1), server_default=text("0"))
    filterSpecialities = Column(TINYINT(1), server_default=text("0"))
    isIgnoreEventExecDate = Column(TINYINT(1), server_default=text("0"), comment='Игнорировать дату окончания события')
    showAPOrg = Column(TINYINT(1), server_default=text("1"))
    showAPNotes = Column(TINYINT(1), server_default=text("1"))
    advancePaymentRequired = Column(TINYINT(1), server_default=text("0"), comment='Флаг: "Требует авансирования"')
    checkPersonSet = Column(TINYINT(1), server_default=text("0"), comment='Флаг: Проверять на наличие исполнителя')
    defaultIsUrgent = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Срочность по умолчанию')
    checkEnterNote = Column(TINYINT(1), server_default=text("0"),
                            comment='Требуется обязательное заполнения примечания. 0 - не требуется 1 - требуется')
    formulaAlias = Column(String(64),
                          comment='Короткий алиас для использования в формулах, используемых в автозаполнении свойств')
    isAllowedAfterDeath = Column(TINYINT(1), server_default=text("0"))
    isAllowedDateAfterDeath = Column(TINYINT(1), server_default=text("0"))
    eventStatusMod = Column(SMALLINT(1), server_default=text("0"))

    createPerson = relationship('Person', primaryjoin='ActionType.createPerson_id == Person.id')
    defaultExecPerson = relationship('Person', primaryjoin='ActionType.defaultExecPerson_id == Person.id')
    defaultSetPerson = relationship('Person', primaryjoin='ActionType.defaultSetPerson_id == Person.id')
    group = relationship('ActionType', remote_side=[id], primaryjoin='ActionType.group_id == ActionType.id')
    modifyPerson = relationship('Person', primaryjoin='ActionType.modifyPerson_id == Person.id')
    nomenclativeService = relationship('RbService')
    prescribedType = relationship('ActionType', remote_side=[id],
                                  primaryjoin='ActionType.prescribedType_id == ActionType.id')
    quotaType = relationship('QuotaType')
    refferalType = relationship('Person', primaryjoin='ActionType.refferalType_id == Person.id')
    shedule = relationship('RbActionShedule')


class OrganisationAccount(Base):
    __tablename__ = 'Organisation_Account'

    id = Column(INTEGER(11), primary_key=True)
    organisation_id = Column(INTEGER(11), nullable=False, comment='АПУ {Organisation}')
    bankName = Column(String(128), nullable=False, comment='Наименование организации в банке')
    name = Column(String(20), nullable=False, comment='Расчетный счет')
    notes = Column(TINYTEXT, nullable=False, comment='Примечания')
    bank_id = Column(ForeignKey('Bank.id'), nullable=False, comment='Банковские реквизиты {Bank}')
    cash = Column(TINYINT(1), nullable=False, comment='Наличные: для кассы')
    personalAccount = Column(String(20), nullable=False, comment='Лицевой счет')

    bank = relationship('Bank')


class RbHighTechCureMethod(Base):
    __tablename__ = 'rbHighTechCureMethod'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(9), nullable=False, comment='Код')
    name = Column(String(400), nullable=False, comment='Название')
    regionalCode = Column(String(8), nullable=False, server_default=text("''"), comment='Региональный код')
    federalCode = Column(String(16), nullable=False, server_default=text("''"), comment='Федеральный код')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка об удалении')
    cureKind_id = Column(ForeignKey('rbHighTechCureKind.id', ondelete='CASCADE'), nullable=False,
                         comment='Вид ВМП {rbHighTechCureKind}')
    beginDate = Column(Date)
    endDate = Column(Date)

    createPerson = relationship('Person', primaryjoin='RbHighTechCureMethod.createPerson_id == Person.id')
    cureKind = relationship('RbHighTechCureKind')
    modifyPerson = relationship('Person', primaryjoin='RbHighTechCureMethod.modifyPerson_id == Person.id')


class Contract(Base):
    __tablename__ = 'Contract'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    number = Column(String(64), nullable=False, comment='Номер договора')
    date = Column(Date, nullable=False, comment='Дата договора')
    recipient_id = Column(INTEGER(11), nullable=False, comment='Получатель {Organisation}')
    recipientAccount_id = Column(ForeignKey('Organisation_Account.id'),
                                 comment='Расчетный счет получателя {OrgAccount}')
    recipientKBK = Column(String(30), nullable=False, comment='КБК получателя')
    payer_id = Column(INTEGER(11), comment='Плательщик {Organisation}')
    payerAccount_id = Column(ForeignKey('Organisation_Account.id'), comment='Расчетный счет плательщика {OrgAccount}')
    payerKBK = Column(String(30), nullable=False, comment='КБК плательщика')
    begDate = Column(Date, nullable=False, comment='Дата начала действия договора')
    endDate = Column(Date, nullable=False, comment='Дата окончания действия договора')
    finance_id = Column(ForeignKey('rbFinance.id'), nullable=False, comment='Тип финансирования договора {rbFinance}')
    grouping = Column(String(64), nullable=False, comment='Строка для группировки и сортировки')
    resolution = Column(String(64), nullable=False, comment='Постановление - основание договора')
    format_id = Column(ForeignKey('rbAccountExportFormat.id', ondelete='SET NULL'),
                       comment='Формат экспорта счетов по этому договору по умолчанию {rbAccountExportFormat}')
    exposeUnfinishedEventVisits = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                         comment='Разрешить выставлять счета по визитам незаконченных событий')
    exposeUnfinishedEventActions = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                          comment='Разрешить выставлять счета по мероприятиям незаконченных событий')
    visitExposition = Column(TINYINT(1), nullable=False, server_default=text("0"),
                             comment='0-визит выставляется  по врачу визита, 1-по врачу события')
    actionExposition = Column(TINYINT(1), nullable=False, server_default=text("0"),
                              comment='0-действие выставляется по врачу действия, 1-по врачу события')
    exposeDiscipline = Column(INTEGER(2), nullable=False, server_default=text("0"),
                              comment='Биты: [0]: byEvent, [123]: byDate (0 - нет, 1-день, 2-неделя, 3-декада, 4-месяц), [4] byClient, [56]: byInsurer (0- нет, 1 - С.К.с филиалами, 2 - С.К.по филиалам)')
    priceList_id = Column(INTEGER(11), comment='Прайс-лист {Contract}')
    coefficient = Column(Float(asdecimal=True), nullable=False, server_default=text("0"),
                         comment='Коэффициент для расчета тарифов')
    coefficientEx = Column(Float(asdecimal=True), nullable=False, server_default=text("0"),
                           comment='Коэффициент расчета тарифа для превышенного количества')
    coefficientEx2 = Column(Float(asdecimal=True), nullable=False, server_default=text("0"),
                            comment='Коэффициент расчета тарифа для второго превышенного количества')
    orgCategory = Column(String(1), nullable=False, comment='Категория ЛПУ')
    regionalTariffRegulationFactor = Column(Float(asdecimal=True), nullable=False, server_default=text("1"),
                                            comment='Коэффициент районного регулирования тарифов')
    exposeByMESMaxDuration = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='Учитывать максимальную длительность по стандарту')
    ignorePayStatusForJobs = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='Игнорировать статус оплаты для работ в журнале выполнения работ')
    assignedClient_id = Column(INTEGER(11),
                               comment='(deprecated in r, see PaymentScheme) Пациент, для которого договор является именным')
    assignedBegDate = Column(Date,
                             comment='(deprecated in r, see PaymentScheme) Начало периода отображения именного договора в обращениях')
    assignedEndDate = Column(Date,
                             comment='(deprecated in r, see PaymentScheme) Конец периода отображения именного договора в обращениях')
    isConsiderFederalPrice = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='1 - учитывать федеральную цену, 2 - не учитывать')
    deposit = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Сумма договора')
    maxClients = Column(INTEGER(11), nullable=False, server_default=text("0"),
                        comment='Максимальное количество пациентов')
    counterValue = Column(String(30), comment='Значение счетчика')
    typeId = Column(INTEGER(11), comment='Тип договора {rbContractType} ')
    limitationPeriod = Column(TINYINT(2), nullable=False, server_default=text("0"),
                              comment='Срок давности при формировании счетов')
    LPU = Column(INTEGER(11))
    exposeWithoutPolicySeparately = Column(TINYINT(1), server_default=text("0"),
                                           comment='Формировать отдельные счета по бесполисным пациентам')

    createPerson = relationship('Person', primaryjoin='Contract.createPerson_id == Person.id')
    finance = relationship('RbFinance')
    format = relationship('RbAccountExportFormat')
    modifyPerson = relationship('Person', primaryjoin='Contract.modifyPerson_id == Person.id')
    payerAccount = relationship('OrganisationAccount', primaryjoin='Contract.payerAccount_id == OrganisationAccount.id')
    recipientAccount = relationship('OrganisationAccount',
                                    primaryjoin='Contract.recipientAccount_id == OrganisationAccount.id')


class TakenTissueJournal(Base):
    __tablename__ = 'TakenTissueJournal'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), ForeignKey('Client.id', ondelete='SET NULL'),
                       comment='Пациент предоставивший образец {Client}')
    tissueType_id = Column(ForeignKey('rbTissueType.id', ondelete='CASCADE'),
                           ForeignKey('rbTissueType.id', ondelete='SET NULL'),
                           comment='Тип забранной ткани {rbTissueType}')
    externalId = Column(String(30), nullable=False, comment='Внешний идентификатор')
    number = Column(String(30), nullable=False, comment='Порядковый номер(позиция в журнале)')
    amount = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='Количество')
    unit_id = Column(ForeignKey('rbUnit.id', ondelete='SET NULL'), comment='Единица измерения {rbUnit}')
    datetimeTaken = Column(DateTime, nullable=False, comment='Дата и время забора')
    execPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Сотрудник выполнивший забор {Person}')
    note = Column(String(128), nullable=False, server_default=text("''"), comment='Примечания')
    status = Column(TINYINT(1), nullable=False, server_default=text("0"),
                    comment='0-в работе, 1-начато, 2-ожидание, 3-закончено, 4-отменено, 5-без резуьтата')

    client = relationship('Client', primaryjoin='TakenTissueJournal.client_id == Client.id')
    client1 = relationship('Client', primaryjoin='TakenTissueJournal.client_id == Client.id')
    createPerson = relationship('Person', primaryjoin='TakenTissueJournal.createPerson_id == Person.id')
    execPerson = relationship('Person', primaryjoin='TakenTissueJournal.execPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='TakenTissueJournal.modifyPerson_id == Person.id')
    tissueType = relationship('RbTissueType', primaryjoin='TakenTissueJournal.tissueType_id == RbTissueType.id')
    tissueType1 = relationship('RbTissueType', primaryjoin='TakenTissueJournal.tissueType_id == RbTissueType.id')
    unit = relationship('RbUnit')


class Event(Base):
    __tablename__ = 'Event'

    id = Column(INTEGER(11), primary_key=True, autoincrement=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(INTEGER(11), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    externalId = Column(String(30), nullable=False, comment='внешний идентификатор полученный при импорте ф131 и т.п.')
    eventType_id = Column(INTEGER(11), nullable=False, comment='Тип события {EventType}')
    org_id = Column(INTEGER(11), comment='Место проведения {Organisation}')
    client_id = Column(ForeignKey('Client.id'), comment='Пациент к которому относится действие {Client}')
    contract_id = Column(INTEGER(11), comment='Договор {Contract}')
    prevEventDate = Column(DateTime, comment='Дата предыдущего события (для указания периодического осмотра в ДМО)')
    setDate = Column(DateTime, nullable=False, comment='Дата начала')
    setPerson_id = Column(INTEGER(11), comment='Направивший сотрудник ЛПУ {Person}')
    execDate = Column(DateTime, comment='Дата выполнения')
    execPerson_id = Column(INTEGER(11), comment='Выполнивший сотрудник ЛПУ {Person}')
    isPrimary = Column(TINYINT(1), nullable=False,
                       comment='Признак первичности (1-первичный, 2-повторный, 3-активное посещение, 4-перевозка, 5-амбулаторно)')
    order = Column(TINYINT(1), nullable=False,
                   comment='Порядок наступления (1-плановый, 2-экстренный, 3-самотёком, 4-принудительный, 5-неотложный)')
    result_id = Column(INTEGER(11), comment='Результат {rbResult}')
    nextEventDate = Column(DateTime, comment='Дата след. явки')
    payStatus = Column(INTEGER(11), nullable=False, comment='Флаги финансирования')
    typeAsset_id = Column(INTEGER(11), comment='Тип актива {rbEmergencyTypeAsset}')
    note = Column(Text, nullable=False, comment='Примечание')
    curator_id = Column(INTEGER(11), comment='Куратор {Person}')
    assistant_id = Column(INTEGER(11), comment='Ассистент {Person}')
    pregnancyWeek = Column(INTEGER(11), nullable=False, server_default=text("0"),
                           comment='Срок беременности, 0-нет беременности')
    MES_id = Column(INTEGER(11), comment='МЭС {mes.MES}')
    mesSpecification_id = Column(INTEGER(11), comment='Особенность выполнения МЭС {rbMesSpecification}')
    relegateOrg_id = Column(INTEGER(11), comment='Направитель {Organisation}')
    totalCost = Column(Float(asdecimal=True), nullable=False, comment='Сумма по услугам')
    patientModel_id = Column(INTEGER(11), comment='Модель пациента {rbPatientModel}')
    cureType_id = Column(INTEGER(11), comment='Вид лечения {rbCureType}')
    cureMethod_id = Column(INTEGER(11), comment='Метод лечения {rbCureMethod}')
    prevEvent_id = Column(INTEGER(11), comment='Является продолжением События{Event}')
    referral_id = Column(INTEGER(11), comment='Направление {Referral}')
    armyReferral_id = Column(INTEGER(11), comment='Направление из военкомата {Referral}')
    littleStranger_id = Column(ForeignKey('Event_LittleStranger.id', ondelete='SET NULL'),
                               comment='Признак новорожденного')
    goal_id = Column(INTEGER(11), comment='Цель обращения {rbEventGoal}')
    outgoingOrg_id = Column(INTEGER(11), comment='Организация, в которую направлен пациент')
    outgoingRefNumber = Column(String(10), server_default=text("''"), comment='Номер исходящего направления')
    hmpKind_id = Column(INTEGER(11), comment='Вид высокотехнологичной помощи {rbHighTechCureKind}')
    hmpMethod_id = Column(INTEGER(11), comment='Метод высокотехнологично помощи {rbHighTechCureMethod}')
    eventCostPrinted = Column(TINYINT(1), nullable=False, server_default=text("0"),
                              comment='Справка о стоимости была распечатана')
    exposeConfirmed = Column(TINYINT(1), nullable=False, server_default=text("0"),
                             comment='Добавлять ли событие к выставлению в счет (имеет значение только для событий, в типе которых exposeConfirmation = 1)')
    ZNOFirst = Column(TINYINT(1), server_default=text("0"), comment='ЗНО установлен впервые')
    ZNOMorph = Column(TINYINT(1), server_default=text("0"), comment='ЗНО подтверждено морфологически')
    hospParent = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='Госпитализация с родителем/представителем')
    clientPolicy_id = Column(ForeignKey('ClientPolicy.id'), comment='Полис пациента {ClientPolicy}')
    cycleDay = Column(INTEGER(11), comment='День цикла (для беременных) [i2582]')
    locked = Column(TINYINT(1), comment='Обращение заблокировано для редактирования')
    dispByMobileTeam = Column(TINYINT(1), server_default=text("0"),
                              comment='Флаг "Диспансеризация(проф.осмотр) проведена мобильной выездной бригадой"')
    duration = Column(INTEGER(11), comment='Длительность лечения')
    isClosed = Column(TINYINT(1), nullable=False, server_default=text("0"),
                      comment='Закрыто событие или нет (0-не закрыто, 1-закрыто)')
    orgStructure_id = Column(INTEGER(11), comment='Подразделение {OrgStructure}')
    isStage = Column(TINYINT(1), server_default=text("0"), comment='Этапное лечение')
    isCrime = Column(TINYINT(1), server_default=text("0"), comment='Криминальный случай')
    signedDocuments = Column(TINYINT(1), nullable=False, server_default=text("0"),
                             comment='Отметка об успешном подписании документа')
    signDateTime = Column(DateTime, comment='Дата подписи')
    KSGCriterion = Column(INTEGER(11), server_default=text("0"), comment='Дополнительный критерий КСГ {rbKSGCriterion}')
    transfId = Column(INTEGER(11), comment='id "Признак поступления" из {rbTransf}')

    clientPolicy = relationship('ClientPolicy')
    littleStranger = relationship('EventLittleStranger')
    client = relationship('Client')


class EventType(Base):
    __tablename__ = 'EventType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    purpose_id = Column(ForeignKey('rbEventTypePurpose.id'),
                        comment='Назначение типа события; цель {rbEventTypePurpose}')
    finance_id = Column(ForeignKey('rbFinance.id', ondelete='SET NULL'), comment='Тип финансирования {rbFinance}')
    scene_id = Column(ForeignKey('rbScene.id', ondelete='SET NULL'), comment='Место визита по умолчанию {rbScene}')
    visitServiceModifier = Column(String(128), nullable=False,
                                  comment='Модификатор сервиса; пусто - нет изменения, "-" - удаляет сервис, "+XXX"-меняет сервис на XXХ, "~/s/r/"-замена по рег.выражению, x - меняет первую букву в коде сервиса')
    visitServiceFilter = Column(String(32), nullable=False, comment='фильтрация списка услуг визитов')
    visitFinance = Column(TINYINT(1), nullable=False, server_default=text("0"),
                          comment='0-по событию, 1-финансирование визита определяется по врачу визита ')
    actionFinance = Column(TINYINT(1), nullable=False, server_default=text("1"),
                           comment='0-aвтоматически не заполнять, 1-по событию, 2-по назначившему, 3-по исполнителю')
    actionContract = Column(TINYINT(1), nullable=False, server_default=text("0"),
                            comment='0-aвтоматически не заполнять, 1-при возможности заполнять по событию')
    period = Column(TINYINT(4), nullable=False, comment='Период, целое число, период в месяцах')
    singleInPeriod = Column(TINYINT(4), nullable=False,
                            comment='Период повторения, целое число 0-нет, 1-неделя, 2-месяц, 3-квартал, 4-полугодие, 5-год')
    isLong = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Является продолжительным')
    dateInput = Column(TINYINT(1), nullable=False, server_default=text("0"),
                       comment='Дисциплина ввода дат при создании события: 0-дата начала, 1-дата окончания, 2-даты начала и окончания')
    service_id = Column(ForeignKey('rbService.id', ondelete='SET NULL'), comment='Базовый сервис ОМС {rbService}')
    context = Column(String(64), nullable=False, comment='Контекст печати ')
    form = Column(String(64), nullable=False,
                  comment='Код формы, используемой для радактирования событий данного типа; что-то вроде "003", "025" etc.')
    minDuration = Column(INTEGER(11), nullable=False, server_default=text("0"),
                         comment='Минимальная длительность события')
    maxDuration = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='Максимальная длительность')
    showStatusActionsInPlanner = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                        comment='Показывать типы действия класса Статус в планировщике')
    showDiagnosticActionsInPlanner = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                            comment='Показывать типы действия класса Диагностика в планировщике')
    showCureActionsInPlanner = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                      comment='Показывать типы действия класса Лечение в планировщике')
    showMiscActionsInPlanner = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                      comment='Показывать типы действия класса Прочие мероприятия в планировщике')
    limitStatusActionsInput = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                     comment='Ограчить ввод действий класса Статус в событии списком из типа события')
    limitDiagnosticActionsInput = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                         comment='Ограчить ввод действий класса Диагностика в событии списком из типа события')
    limitCureActionsInput = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                   comment='Ограчить ввод действий класса Лечение в событии списком из типа события')
    limitMiscActionsInput = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                   comment='Ограчить ввод действий класса Прочие мероприятия в событии списком из типа события')
    showTime = Column(TINYINT(1), nullable=False, server_default=text("0"),
                      comment='Показывать в интерфейсе не только дату, но и время назначения/окончания')
    medicalAidKind_id = Column(ForeignKey('rbMedicalAidKind.id'), comment='Вид мед.помощи {rbMedicalAidKind}')
    medicalAidType_id = Column(ForeignKey('rbMedicalAidType.id'), comment='Тип мед.помощи {rbMedicalAidType}')
    eventProfile_id = Column(ForeignKey('rbEventProfile.id', ondelete='SET NULL'),
                             comment='Профиль события {rbEventProfile}')
    mesRequired = Column(INTEGER(1), nullable=False, server_default=text("0"), comment='Требуется указание МЭС')
    defaultMesSpecification_id = Column(INTEGER(11),
                                        comment='Особенность выполнения МЭС по умолчанию {rbMesSpecification}')
    mesCodeMask = Column(String(64), server_default=text("''"), comment='Шаблон кода МЭС (для like)')
    mesNameMask = Column(String(64), server_default=text("''"), comment='Шаблон имени МЭС (для like)')
    counter_id = Column(ForeignKey('rbCounter.id'), comment='Счетчик события {rbCounter}')
    isExternal = Column(TINYINT(1), nullable=False, server_default=text("0"),
                        comment='Требуется ввод внешнего идентификатора')
    # generateExternalIdOnSave = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Устаревшее поле, подлежит удалению при использовании ревизий вне промежутка 14494-14800')
    externalIdAsAccountNumber = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                       comment='Использовать внешний идентификатор в качестве номера счета')
    counterType = Column(TINYINT(1), nullable=False, server_default=text("0"),
                         comment='Использование счетчика (0-не используется, 1-при создании обращения, 2-при сохранении, 3-при изменении результата обращения)')
    hasAssistant = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Требуется ввод ассистента')
    hasCurator = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Требуется ввод куратора')
    hasVisitAssistant = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='Требуется ввод ассистента визита')
    canHavePayableActions = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                   comment='Признак: может иметь платные услуги')
    isRequiredCoordination = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='Требуется обязательное согласование')
    isOrgStructurePriority = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='Приоритет подразделения для функции "Добавить ..." в событии')
    isTakenTissue = Column(TINYINT(1), nullable=False, server_default=text("0"),
                           comment='0-не использует забор тканей, 1-использует забор тканей')
    isSetContractNumFromCounter = Column(TINYINT(4),
                                         comment='Флаг назначения договору номера из счетчика источника финансирования (i1560)')
    sex = Column(TINYINT(4), nullable=False, server_default=text("0"),
                 comment='Применимо для указанного пола (0-любой, 1-М, 2-Ж)')
    age = Column(String(80), nullable=False,
                 comment='Применимо для указанного интервала возрастов пусто-нет ограничения, "{NNN{д|н|м|г}-{MMM{д|н|м|г}}" - с NNN дней/недель/месяцев/лет по MMM дней/недель/месяцев/лет; пустая нижняя или верхняя граница - нет ограничения снизу или сверху')
    permitAnyActionDate = Column(TINYINT(1), nullable=False)
    isOnJobPayedFilter = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='флаг необходимости учета настройки вывода работ по оплате')
    prefix = Column(String(8), comment='Префикс внешнего идентификатора')
    exposeGrouped = Column(SMALLINT(6), nullable=False, server_default=text("0"),
                           comment='Группировать при выгрузке с другими событиями')
    showLittleStranger = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='Показывать блок "Признак новорожденного" (0-нет, 1-да)')
    uniqueExternalId = Column(TINYINT(1), nullable=False, server_default=text("1"),
                              comment='Проверять внешний идентификатор на уникальность')
    uniqueExternalIdInThisYear = Column(TINYINT(1), server_default=text("0"),
                                        comment='Проверять на уникальность в текущем году')
    defaultOrder = Column(TINYINT(4), nullable=False, server_default=text("1"),
                          comment='Порядок наступления по умолчанию')
    inheritDiagnosis = Column(TINYINT(4), nullable=False, server_default=text("0"),
                              comment='Наследовать диагноз из предыдущего обращения')
    diagnosisSetDateVisible = Column(INTEGER(1), nullable=False, server_default=text("0"),
                                     comment='Визуализация столбца "Дата выявления диагноза"')
    isResetSetDate = Column(TINYINT(1), nullable=False, server_default=text("0"),
                            comment='Признак необходимости сбрасывать дату начала обращения на текущую перед созданием')
    isAvailInFastCreateMode = Column(TINYINT(1), nullable=False, server_default=text("1"),
                                     comment='Доступен в режиме быстрого создания обращения (i1308)')
    caseCast_id = Column(ForeignKey('rbCaseCast.id', onupdate='CASCADE'), comment='Тип случая лечения {rbCaseCast}')
    defaultEndTime = Column(Time, comment='Время окончания события по умолчанию')
    isCheck_KSG = Column(TINYINT(1), comment='Имеется ли проверка КСГ ?: NULL,0 - нет; 1 - мягкая; 2 - жесткая')
    weekdays = Column(TINYINT(1), nullable=False, server_default=text("5"), comment='Продолжительность рабочей недели')
    exposeConfirmation = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='Надо ли явно указывать, что событие может быть добавлено в счет: 0-нет, 1-да')
    needMesPerformPercent = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                   comment='Настройка, отвечающая за то, какой процент услуг должен быть обязательно выполнен для данного МЭС')
    showZNO = Column(TINYINT(1), server_default=text("0"), comment='отображать ввод ЗНО в интерфейсе')
    goalFilter = Column(TINYINT(1), server_default=text("0"), comment='Фильтровать типы действия по цели')
    setFilterStandard = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='Набор фильтров для подстановки Стандарта (0 - набор фильтров для МЭС, 1 - набор фильтров для КСГ')
    inheritResult = Column(TINYINT(1), server_default=text("1"), comment='Наследовать результат обращения')
    eventKind_id = Column(ForeignKey('rbEventKind.id'), comment='Вид события')
    payerAutoFilling = Column(TINYINT(1), server_default=text("0"), comment='Проверять на уникальность в текущем году')
    filterPosts = Column(TINYINT(1), server_default=text("0"))
    filterSpecialities = Column(TINYINT(1), server_default=text("0"))
    dispByMobileTeam = Column(TINYINT(1), server_default=text("0"),
                              comment='Отображать флаг "Диспансеризация(проф.осмотр) проведена мобильной выездной бригадой"')
    compulsoryServiceStopIgnore = Column(TINYINT(1), server_default=text("0"),
                                         comment='Игнорирование запрета на обслуживание ОМС')
    voluntaryServiceStopIgnore = Column(TINYINT(1), server_default=text("0"),
                                        comment='Игнорирование запрета на обслуживание ДМС')
    inheritGoal = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Наследовать цель обращения')
    netrica_Code = Column(String(65), comment='1.2.643.5.1.13.2.1.1.106')
    availableForExternal = Column(TINYINT(1))
    reqDN = Column(TINYINT(1))
    reqHealthGroup = Column(TINYINT(1))
    isAddTreatmentToDeath = Column(TINYINT(1), nullable=False)
    needReferal = Column(TINYINT(1), server_default=text("0"),
                         comment='Требуется заполнение Направления (Доп. данных) 0 - не требуется 1 - требуется')
    referalDateActualityDays = Column(INTEGER(11), server_default=text("0"),
                                      comment='Актуальность даты направления - поле для ввода кол-во дней')
    eventGoal = Column(INTEGER(11), comment='Цель обращения {rbEventGoal}')
    result = Column(INTEGER(11), comment='Результат события {rbResult}')
    MKB = Column(String(8), comment='Результат события {MKB}')
    chk_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Включить проверки и умолчания ЗНО')
    chkMKB_ZNO = Column(TINYINT(1), server_default=text("0"), comment='МКБ')
    chkReason_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Повод обращения')
    chkstady_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Стадия заболевания')
    chkstady_T_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Стадия T')
    chkstady_N_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Стадия N')
    chkstady_M_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Стадия M')
    chkDate_ZNO = Column(TINYINT(1), server_default=text("0"), comment='Дата взятия материала')
    chkConsiliumData = Column(TINYINT(1), server_default=text("0"), comment='Консилиум')
    inheritCheckupResult = Column(TINYINT(1), server_default=text("1"), comment='Наследовать результат осмотра')
    isKSGCriterion = Column(TINYINT(1), server_default=text("0"), comment='Отображать дополнительный критерий КСГ')
    isKslpShow = Column(TINYINT(1), server_default=text("0"), comment='Отображать комбобокс КСЛП')
    # chk_SendInIEMK = Column(TINYINT(1), server_default=text("0"), comment='Отображать комбобокс Автоматически отправлять случай в ИЭМК')
    chkSurgeryCure = Column(TINYINT(1), server_default=text("0"), comment='Хирургическое лечение')
    chkPillsTherapy = Column(TINYINT(1), server_default=text("0"), comment='Лекарственная противоопухолевая терапия')
    chkRadiationTherapy = Column(TINYINT(1), server_default=text("0"), comment='Лучевая терапия')
    chkChemyTherapy = Column(TINYINT(1), server_default=text("0"), comment='Химиолучевая терапия')
    # isSeveralEvents = Column(TINYINT(1), server_default=text("0"))
    isWithoutResponsiblePerson = Column(TINYINT(1), server_default=text("0"),
                                        comment='Не требовать выбор ответственного за событие при создании')
    chkTransf = Column(TINYINT(1), nullable=False, server_default=text("0"),
                       comment='Чекбокс "Признак поступления" (0 - выкл, 1 - вкл)')
    transfId = Column(INTEGER(11), comment='id "Признак поступления" из {rbTransf}')
    canSend = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Выгружать во внешние системы')

    caseCast = relationship('RbCaseCast')
    counter = relationship('RbCounter')
    createPerson = relationship('Person', primaryjoin='EventType.createPerson_id == Person.id')
    eventKind = relationship('RbEventKind')
    eventProfile = relationship('RbEventProfile')
    finance = relationship('RbFinance')
    medicalAidKind = relationship('RbMedicalAidKind')
    medicalAidType = relationship('RbMedicalAidType')
    modifyPerson = relationship('Person', primaryjoin='EventType.modifyPerson_id == Person.id')
    purpose = relationship('RbEventTypePurpose')
    scene = relationship('RbScene')
    service = relationship('RbService')


class RbCounter(Base):
    __tablename__ = 'rbCounter'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    value = Column(BIGINT(11), nullable=False, server_default=text("0"), comment='Текущее значение счетчика')
    prefix = Column(String(32), comment='Префикс')
    postfix = Column(String(32), comment='Постфикс')
    separator = Column(String(8), server_default=text("' '"), comment='Разделитель')
    reset = Column(INTEGER(1), nullable=False, server_default=text("0"),
                   comment='0-Не сбрасывается, 1-Через сутки,2-Через неделю,3-через месяц,4-через квартал, 5-через полугодие, 6-через год')
    startDate = Column(Date, nullable=False, comment='Дата начала работы счетчика')
    resetDate = Column(Date, comment='Дата последнего сброса')
    sequenceFlag = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Флаг последовательности')

    createPerson = relationship('Person', primaryjoin='RbCounter.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbCounter.modifyPerson_id == Person.id')


class RbEventKind(Base):
    __tablename__ = 'rbEventKind'

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(16), nullable=False)
    name = Column(String(128), nullable=False, comment='Вид события')


class RbEventProfile(Base):
    __tablename__ = 'rbEventProfile'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(16), nullable=False, comment='Код')
    regionalCode = Column(String(16), nullable=False, comment='Региональный код')
    name = Column(String(64), nullable=False, comment='Наименование')

    createPerson = relationship('Person', primaryjoin='RbEventProfile.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbEventProfile.modifyPerson_id == Person.id')


class RbEventTypePurpose(Base):
    __tablename__ = 'rbEventTypePurpose'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    regionalCode = Column(String(16), nullable=False, server_default=text("''"), comment='Региональный код')
    name = Column(String(64), nullable=False, comment='Наименование')
    federalCode = Column(String(8), nullable=False, comment='Федеральный код')

    createPerson = relationship('Person', primaryjoin='RbEventTypePurpose.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbEventTypePurpose.modifyPerson_id == Person.id')


class RbScene(Base):
    __tablename__ = 'rbScene'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи (внешний id)')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    code = Column(String(8), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    serviceModifier = Column(String(128), nullable=False,
                             comment='Модификатор сервиса; пусто - нет изменения, "-" - удаляет сервис, "+XXX"-меняет сервис на XXХ, "~/s/r/"-замена по рег.выражению, x - меняет первую букву в коде сервиса')
    netrica_Code = Column(String(65), comment='1.2.643.2.69.1.1.1.18')

    createPerson = relationship('Person', primaryjoin='RbScene.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbScene.modifyPerson_id == Person.id')


class Action(Base):
    __tablename__ = 'Action'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    actionType_id = Column(ForeignKey('ActionType.id'), nullable=False, comment='Тип события {ActionType}')
    specifiedName = Column(String(255), nullable=False, server_default=text("''"),
                           comment='Уточнённое наименование (лек. средство, операция и т.п.)')
    event_id = Column(ForeignKey('Event.id', ondelete='CASCADE'),
                      comment='Событие, к которому относится действие {Event}')
    idx = Column(INTEGER(11), nullable=False, server_default=text("0"),
                 comment='Индекс в списке событий (для сортировки в списке)')
    directionDate = Column(DateTime, comment='Дата назначения')
    status = Column(TINYINT(4), nullable=False,
                    comment='Статус выполнения: 0-Начато, 1-Ожидание, 2-Закончено, 3-Отменено, 4-Без результата')
    setPerson_id = Column(ForeignKey('Person.id'), comment='Назначивший {Person}')
    isUrgent = Column(INTEGER(1), nullable=False, server_default=text("0"), comment='Является срочным')
    begDate = Column(DateTime, comment='Дата начала работы')
    plannedEndDate = Column(DateTime, nullable=False, comment='Плановая дата выполнения')
    endDate = Column(DateTime, comment='Дата окончания работы')
    note = Column(Text, nullable=False, comment='Примечания')
    referralPurpose = Column(Text)
    referredPerson = Column(Text)
    person_id = Column(ForeignKey('Person.id'), comment='Исполнитель {Person}')
    office = Column(String(16), nullable=False, comment='Кабинет')
    amount = Column(Float(asdecimal=True), nullable=False, comment='Количество')
    uet = Column(Float(asdecimal=True), server_default=text("0"), comment='УЕТ (Условные Единицы Трудозатрат)')
    expose = Column(INTEGER(1), nullable=False, server_default=text("1"), comment='Выставлять счёт')
    payStatus = Column(INTEGER(11), nullable=False, comment='Флаги финансирования')
    account = Column(TINYINT(1), nullable=False, comment='Флаг Считать')
    MKB = Column(String(8), nullable=False, comment='Шифр МКБ действия(не учитывается в ЛУД)')
    morphologyMKB = Column(String(16), nullable=False, comment='Морфология диагноза МКБ')
    finance_id = Column(ForeignKey('rbFinance.id', ondelete='SET NULL'), comment='тип финансирования {rbFinance}')
    contract_id = Column(ForeignKey('Contract.id', ondelete='SET NULL'), comment='договор {Contract}')
    prescription_id = Column(ForeignKey('Action.id', ondelete='SET NULL', onupdate='CASCADE'),
                             comment='Ссылка на назначение {Action}')
    takenTissueJournal_id = Column(ForeignKey('TakenTissueJournal.id', ondelete='SET NULL'),
                                   comment='Ссылка на журнал забора тканей {TakenTissueJournal}')
    org_id = Column(ForeignKey('Organisation.id'), comment='Организация выполнившая действие {Organisation}')
    coordDate = Column(DateTime, comment='Дата и время согласования')
    coordAgent = Column(String(128), nullable=False, server_default=text("''"),
                        comment='Сотрудник ЛПУ, согласовавший действие')
    coordInspector = Column(String(128), nullable=False, server_default=text("''"),
                            comment='Представитель плательщика (сотрудник СМО), согласовавший действие')
    coordText = Column(TINYTEXT, nullable=False, comment='Текст согласования')
    assistant_id = Column(ForeignKey('Person.id', ondelete='SET NULL', onupdate='CASCADE'),
                          comment='(deprecated in r16412, see Action_Assistant) Ассистент {Person}')
    preliminaryResult = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='Предварительный результат 0-не определен, 1-получен, 2-без результата')
    duration = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='Длительность')
    periodicity = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='Периодичность')
    aliquoticity = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='Кратность')
    signature = Column(INTEGER(11), nullable=False, server_default=text("0"))
    assistant2_id = Column(ForeignKey('Person.id', ondelete='SET NULL'),
                           comment='(deprecated in r16412, see Action_Assistant) Второй ассистент {Person}')
    assistant3_id = Column(ForeignKey('Person.id', ondelete='SET NULL'),
                           comment='(deprecated in r16412, see Action_Assistant) Третий ассистент {Person}')
    packPurchasePrice = Column(Float(asdecimal=True), nullable=False, server_default=text("0"),
                               comment='Закупочная стоимость упаковки')
    doseRatePrice = Column(Float(asdecimal=True), nullable=False, server_default=text("0"),
                           comment='Закупочная стоимость упаковки')
    MES_id = Column(INTEGER(11), comment='МЭС {mes.MES}')
    counterValue = Column(String(30), comment='значение счетчика типов действия')
    customSum = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Ручной ввод цены')
    parent_id = Column(INTEGER(11), comment='Ссылка на родительское действие')
    hmpKind_id = Column(ForeignKey('rbHighTechCureKind.id'),
                        comment='Вид высокотехнологичной помощи {rbHighTechCureKind}')
    hmpMethod_id = Column(ForeignKey('rbHighTechCureMethod.id'),
                          comment='Метод высокотехнологично помощи {rbHighTechCureMethod}')
    isVerified = Column(TINYINT(1), server_default=text("0"),
                        comment='Флаг указывающий проверяли ли выполнение экшена. {i3592}')
    importDate = Column(DateTime, comment='Дата импорта действия из Внешней Системы')

    actionType = relationship('ActionType')
    assistant2 = relationship('Person', primaryjoin='Action.assistant2_id == Person.id')
    assistant3 = relationship('Person', primaryjoin='Action.assistant3_id == Person.id')
    assistant = relationship('Person', primaryjoin='Action.assistant_id == Person.id')
    contract = relationship('Contract')
    createPerson = relationship('Person', primaryjoin='Action.createPerson_id == Person.id')
    event = relationship('Event')
    finance = relationship('RbFinance')
    hmpKind = relationship('RbHighTechCureKind')
    hmpMethod = relationship('RbHighTechCureMethod')
    modifyPerson = relationship('Person', primaryjoin='Action.modifyPerson_id == Person.id')
    org = relationship('Organisation')
    person = relationship('Person', primaryjoin='Action.person_id == Person.id')
    prescription = relationship('Action', remote_side=[id])
    setPerson = relationship('Person', primaryjoin='Action.setPerson_id == Person.id')
    takenTissueJournal = relationship('TakenTissueJournal')


class ActionProperty(Base):
    __tablename__ = 'ActionProperty'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    action_id = Column(ForeignKey('Action.id', ondelete='CASCADE'), nullable=False,
                       comment='Действие к которому относится это свойство {Action}')
    type_id = Column(ForeignKey('ActionPropertyType.id', ondelete='CASCADE'), nullable=False,
                     comment='Тип свойства {ActionPropertyType}')
    unit_id = Column(ForeignKey('rbUnit.id'), comment='Единица измерения {rbUnit}')
    norm = Column(String(64), nullable=False, comment='Норматив')
    isAssigned = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='0=ничего, 1=назначен')
    evaluation = Column(TINYINT(1), comment='оценка, NULL-не назначена, -2,-1 - ниже нормы, 0-норма, 1,2-выше нормы')
    isAutoFillCancelled = Column(TINYINT(1), server_default=text("0"),
                                 comment='Флаг для отмены возможности заполнять свойство автоматически(DEV_VM-1249)')

    action = relationship('Action')
    createPerson = relationship('Person', primaryjoin='ActionProperty.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ActionProperty.modifyPerson_id == Person.id')
    type = relationship('ActionPropertyType')
    unit = relationship('RbUnit')


class ActionPropertyType(Base):
    __tablename__ = 'ActionPropertyType'

    id = Column(INTEGER(11), primary_key=True)
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    actionType_id = Column(ForeignKey('ActionType.id'), nullable=False,
                           comment='Тип действия, к которому относится это свойство {ActionType}')
    idx = Column(INTEGER(11), nullable=False, server_default=text("0"),
                 comment='относительный индекс (для сортировки в списке)')
    template_id = Column(INTEGER(11), comment='Ссылка на библиотеку {ActionPropertyTemplate}')
    name = Column(String(326), nullable=False, comment='Наименование свойства')
    shortName = Column(String(16), nullable=False, comment='Короткое наименование')
    descr = Column(String(128), nullable=False, comment='Описание свойства')
    unit_id = Column(ForeignKey('rbUnit.id'), comment='Единица измерения {rbUnit}')
    typeName = Column(String(64), nullable=False, comment='Имя типа значения, строка "integer","time" и т.п.')
    valueDomain = Column(Text, nullable=False, comment='для типов enum и вариант - наборы строчных значений через |')
    defaultValue = Column(LONGTEXT)
    isVector = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Это векторное значение')
    norm = Column(String(64), nullable=False, comment='Норматив')
    sex = Column(TINYINT(4), nullable=False, comment='Применимо для указанного пола (0-любой, 1-М, 2-Ж)')
    age = Column(String(9), nullable=False,
                 comment='Применимо для указанного интервала возрастов пусто-нет ограничения, "{NNN{д|н|м|г}-{MMM{д|н|м|г}}" - с NNN дней/недель/месяцев/лет по MMM дней/недель/месяцев/лет; пустая нижняя или верхняя граница - нет ограничения снизу или сверху')
    penalty = Column(INTEGER(3), nullable=False, server_default=text("0"), comment='Штраф в баллах(max 100)')
    penaltyUserProfile = Column(Text,
                                comment='Список профилей прав, которых касается штраф. Сепаратор - ";". Sorry for this shit =(')
    visibleInJobTicket = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='0=не видимо при редактировании Job_Ticket, 1=видимо')
    visibleInTableRedactor = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                    comment='0-Не видно, 1-Режим редактирвоания, 2-Без редактирования')
    isAssignable = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='является назначаемым')
    test_id = Column(ForeignKey('rbTest.id', ondelete='SET NULL'),
                     comment='Если свойство является показателем теста, то это ссылка на показатель {rbTest}')
    defaultEvaluation = Column(TINYINT(1), nullable=False, server_default=text("0"),
                               comment='0-не определять, 1-автомат, 2-полуавтомат, 3-ручное')
    canChangeOnlyOwner = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='Право редактировать свойство: 0 - все, 1 - назначивший действие, 2 - никто')
    isActionNameSpecifier = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                   comment='Является уточняющим имя действия')
    laboratoryCalculator = Column(String(3),
                                  comment='три знака: первый-клавиша калькулятора, второй-тип результата(А абсалютное значение, % относительное), третий-группа')
    inActionsSelectionTable = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                     comment='0-Не определено, 1-Recipe(Возьми), 2-Doses(Доза), 3-Signa(Выдай)')
    redactorSizeFactor = Column(TINYINT(1), nullable=False, server_default=text("0"),
                                comment='Коофицент размера редактора свойства действия')
    isFrozen = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Свойство закреплено (0-нет, 1-да)')
    typeEditable = Column(TINYINT(1), nullable=False, server_default=text("1"),
                          comment='Конструктор доступен для редактирования')
    visibleInDR = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='0=не видимо, 1=видимо')
    userProfile_id = Column(ForeignKey('rbUserProfile.id', ondelete='SET NULL', onupdate='CASCADE'),
                            comment='Профиль прав, необходимый для редактирования/просмотра {rbUserProfile}')
    userProfileBehaviour = Column(TINYINT(4), nullable=False, server_default=text("0"),
                                  comment='Поведение при отсутствии прав: 0 - отключать редактир. 1 - скрывать')
    copyModifier = Column(TINYINT(4), nullable=False, server_default=text("0"), comment='Модификатор копирования')
    isVitalParam = Column(TINYINT(1), nullable=False, server_default=text("0"),
                          comment='Является витальным параметром (0-нет, 1-да)')
    vitalParamId = Column(INTEGER(11), comment='Тип витального параметра {rbVitalParams}')
    isODIIParam = Column(TINYINT(1), nullable=False, server_default=text("0"),
                         comment='Является параметром ОДИИ (0-нет, 1-да)')
    ticketsNeeded = Column(TINYINT(4),
                           comment='Количество номерков(JobTicket) необходимое для проведения услуги данного типа')
    customSelect = Column(Text,
                          comment='Поле для пользовательского запроса, использующегося при автоматическом заполнении свойства')
    autoFieldUserProfile = Column(Text,
                                  comment='Список профилей прав, которые могут редактировать автоматически заполняемые поля. Сепаратор - ";"')
    formulaAlias = Column(String(64),
                          comment='Короткий алиас для использования в формулах, используемых в автозаполнении свойств')
    parent_id = Column(INTEGER(11))
    penaltyDiagnosis = Column(String(20))

    actionType = relationship('ActionType')
    test = relationship('RbTest')
    unit = relationship('RbUnit')
    userProfile = relationship('RbUserProfile')


class ActionPropertyHospitalBed(Base):
    __tablename__ = 'ActionProperty_HospitalBed'

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False, comment='{ActionProperty}')
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"),
                   comment='Индекс элемента векторного значения или 0')
    value = Column(ForeignKey('OrgStructure_HospitalBed.id', ondelete='CASCADE', onupdate='CASCADE'),
                   comment='собственно значение {OrgStructure_HospitalBed}')

    ActionProperty = relationship('ActionProperty')
    OrgStructure_HospitalBed = relationship('OrgStructureHospitalBed')


class ActionPropertyInteger(Base):
    __tablename__ = 'ActionProperty_Integer'

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False, comment='{ActionProperty}')
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"),
                   comment='Индекс элемента векторного значения или 0')
    value = Column(INTEGER(11), nullable=False, comment='собственно значение')

    ActionProperty = relationship('ActionProperty')


class ActionPropertyPerson(Base):
    __tablename__ = 'ActionProperty_Person'

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False, comment='{ActionProperty}')
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"),
                   comment='Индекс элемента векторного значения или 0')
    value = Column(INTEGER(11), nullable=False, comment='собственно значение')

    ActionProperty = relationship('ActionProperty')


class ActionPropertyString(Base):
    __tablename__ = 'ActionProperty_String'

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False, comment='{ActionProperty}')
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"),
                   comment='Индекс элемента векторного значения или 0')
    value = Column(Text, nullable=False, comment='собственно значение')

    ActionProperty = relationship('ActionProperty')


class ActionPropertyReference(Base):
    __tablename__ = 'ActionProperty_Reference'

    id = Column(INTEGER(11), primary_key=True, nullable=False)
    index = Column(INTEGER(11), primary_key=True, nullable=False)
    value = Column(INTEGER(11))


class ActionPropertyReserved(Base):
    __tablename__ = 'ActionProperty_Reserved'

    id = Column(INTEGER(11), primary_key=True, nullable=False)
    index = Column(INTEGER(11), primary_key=True, nullable=False)
    value = Column(INTEGER(11))


class ActionPropertyAction(Base):
    __tablename__ = 'ActionProperty_Action'

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False, comment='{ActionProperty}')
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"),
                   comment='Индекс элемента векторного значения или 0')
    value = Column(ForeignKey('Action.id', ondelete='CASCADE', onupdate='CASCADE'),
                   comment='собственно значение {Action}')
    egiszId = Column(INTEGER(11), comment='Идентификатор записи в егисз')

    ActionProperty = relationship('ActionProperty')
    Action = relationship('Action')


class ActionPropertyRbReasonOfAbsence(Base):
    __tablename__ = 'ActionProperty_rbReasonOfAbsence'
    __table_args__ = {'comment': 'Значение свойства действия'}

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False)
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"))
    value = Column(ForeignKey('rbReasonOfAbsence.id', ondelete='CASCADE', onupdate='CASCADE'))

    ActionProperty = relationship('ActionProperty')
    rbReasonOfAbsence = relationship('RbReasonOfAbsence')


class RbReasonOfAbsence(Base):
    __tablename__ = 'rbReasonOfAbsence'
    __table_args__ = {'comment': 'Причина отсутствия'}

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    code = Column(String(8), nullable=False)
    name = Column(String(64), nullable=False)

    createPerson = relationship('Person', primaryjoin='RbReasonOfAbsence.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbReasonOfAbsence.modifyPerson_id == Person.id')


class ActionPropertyTime(Base):
    __tablename__ = 'ActionProperty_Time'

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False, comment='{ActionProperty}')
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"),
                   comment='Индекс элемента векторного значения или 0')
    value = Column(Time, nullable=False, comment='собственно значение')

    ActionProperty = relationship('ActionProperty')


class Session(Base):
    __tablename__ = 'Session'
    __table_args__ = {'comment': 'Сессии пользователей. Используется для авторизации.'}

    id = Column(INTEGER(11), primary_key=True)
    CreateDateTime = Column(DateTime)
    person_id = Column(INTEGER(11))
    access_token = Column(CHAR(128))
    access_expire = Column(DateTime)
    refresh_token = Column(CHAR(128))
    refresh_expire = Column(DateTime)


class SessionOfUser(Session):
    user_id = Column(INTEGER(11))


class RbHelp(Base):
    __tablename__ = 'rbHelp'
    __table_args__ = {'comment': 'Справочная информация'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(256))
    text = Column(LONGTEXT)
    deleted = Column(TINYINT(4))


class RbUserRight(Base):
    __tablename__ = 'rbUserRight'
    __table_args__ = {'comment': 'Права пользователей'}

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    code = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)

    createPerson = relationship('Person', primaryjoin='RbUserRight.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbUserRight.modifyPerson_id == Person.id')


class PersonUserProfile(Base):
    __tablename__ = 'Person_UserProfile'
    __table_args__ = {'comment': 'Связь между пользователем и набором его профилей прав.'}

    id = Column(INTEGER(11), primary_key=True)
    person_id = Column(ForeignKey('Person.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    userProfile_id = Column(ForeignKey('rbUserProfile.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL', onupdate='CASCADE'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id', ondelete='SET NULL', onupdate='CASCADE'))

    createPerson = relationship('Person', primaryjoin='PersonUserProfile.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='PersonUserProfile.modifyPerson_id == Person.id')
    person = relationship('Person', primaryjoin='PersonUserProfile.person_id == Person.id')
    userProfile = relationship('RbUserProfile')


class RbUserProfileRight(Base):
    __tablename__ = 'rbUserProfile_Right'
    __table_args__ = {'comment': 'Профили пользователей'}

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    master_id = Column(ForeignKey('rbUserProfile.id', ondelete='CASCADE'), nullable=False)
    userRight_id = Column(ForeignKey('rbUserRight.id', ondelete='CASCADE'), nullable=False)

    createPerson = relationship('Person', primaryjoin='RbUserProfileRight.createPerson_id == Person.id')
    master = relationship('RbUserProfile')
    modifyPerson = relationship('Person', primaryjoin='RbUserProfileRight.modifyPerson_id == Person.id')
    userRight = relationship('RbUserRight')


class ClientRemark(Base):
    __tablename__ = 'ClientRemark'
    __table_args__ = {'comment': 'Пометки пациента.'}

    id = Column(INTEGER(11), primary_key=True)
    remarkType_id = Column(ForeignKey('rbClientRemarkType.id'), nullable=False)
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    date = Column(Date)
    note = Column(String(255), nullable=False)

    client = relationship('Client')
    remarkType = relationship('RbClientRemarkType')


class RbClientRemarkType(Base):
    __tablename__ = 'rbClientRemarkType'
    __table_args__ = {'comment': 'Справочник типов пометок паицента.'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(16), nullable=False)
    name = Column(String(128), nullable=False)
    flatCode = Column(String(32), nullable=False)


class RbSNILSMissingReason(Base):
    __tablename__ = 'rbSNILSMissingReason'
    __table_args__ = {'comment': 'Причины отсутствия СНИЛС {1.2.643.5.1.13.13.99.2.600}'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(String(64))


class ForeignHospitalization(Base):
    __tablename__ = 'ForeignHospitalization'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id'), nullable=False, comment='Пациент {Client}')
    org_id = Column(ForeignKey('Organisation.id'), nullable=False, comment='ЛПУ {Organisation}')
    purpose_id = Column(ForeignKey('rbHospitalizationPurpose.id'), nullable=False,
                        comment='Цель госпитализации {rbHospitalizationPurpose}')
    MKB = Column(String(10), nullable=False, comment='Код по МКБ')
    clinicDiagnosis = Column(String(128), comment='Клинический диагноз')
    startDate = Column(Date, nullable=False, comment='Дата поступления')
    endDate = Column(Date, nullable=False, comment='Дата выбытия')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ForeignHospitalization.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ForeignHospitalization.modifyPerson_id == Person.id')
    org = relationship('Organisation')
    purpose = relationship('RbHospitalizationPurpose')


class RbHospitalizationPurpose(Base):
    __tablename__ = 'rbHospitalizationPurpose'

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(32), nullable=False, comment='Код, определяющий цель госпитализации')
    name = Column(String(256), nullable=False, comment='Наименование цели')


class ClientInfoSource(Base):
    __tablename__ = 'ClientInfoSource'

    id = Column(INTEGER(11), primary_key=True)
    createDateTime = Column(DateTime, server_default=text("current_timestamp()"), comment='Дата создания записи')
    modifyDateTime = Column(DateTime, server_default=text("current_timestamp()"), comment='Дата изменения записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    client_id = Column(ForeignKey('Client.id'), comment='Пациент {Client}')
    rbInfoSource_id = Column(ForeignKey('rbInfoSource.id', ondelete='SET NULL'),
                             comment='Источник информации {rbInfoSource}')
    infoSourceDate = Column(Date, comment='Дата создания записи')
    docDoc = Column(TINYINT(1), comment='Галочка `ДокДок`')
    onMend = Column(TINYINT(1), comment='Галочка `На поправку`')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientInfoSource.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientInfoSource.modifyPerson_id == Person.id')
    rbInfoSource = relationship('RbInfoSource')


class ClientAllergy(Base):
    __tablename__ = 'ClientAllergy'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False,
                       comment='Прикреплённое лицо {Client}')
    nameSubstance = Column(String(128), nullable=False, comment='Наименование вещества')
    power = Column(INTEGER(11), nullable=False, comment='Степень непереносимости')
    createDate = Column(Date, comment='Дата установления непереносимости')
    notes = Column(TINYTEXT, nullable=False, comment='Примечание')
    reactionCode_id = Column(INTEGER(11), comment='Реакция {rbReactionCode}')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientAllergy.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientAllergy.modifyPerson_id == Person.id')


class ClientIntoleranceMedicament(Base):
    __tablename__ = 'ClientIntoleranceMedicament'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Отметка удаления записи')
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False,
                       comment='Прикреплённое лицо {Client}')
    nameMedicament = Column(String(128), nullable=False, comment='Название медикамента')
    power = Column(INTEGER(11), nullable=False, comment='Степень непереносимости')
    createDate = Column(Date, comment='Дата установления непереносимости')
    notes = Column(TINYTEXT, nullable=False, comment='Примечание')
    reactionCode_id = Column(INTEGER(11), comment='Реакция {rbReactionCode}')
    allergyDrug_id = Column(INTEGER(11), comment='Препарат {InternationalPillsNames}')

    client = relationship('Client')
    createPerson = relationship('Person', primaryjoin='ClientIntoleranceMedicament.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='ClientIntoleranceMedicament.modifyPerson_id == Person.id')


class ClientAnthropometric(Base):
    __tablename__ = 'ClientAnthropometric'

    id = Column(INTEGER(11), primary_key=True)
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                       comment='Идентификатор пациента {Client}')
    # event_id = Column(INTEGER(11), nullable=False, comment='Идентификатор события {Event}')
    date = Column(Date, nullable=False, comment='Дата измерения')
    height = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Рост пациента (см)')
    weight = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Вес пациента (кг)')
    waist = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Обхват талии (см)')
    bust = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Обхват груди (см)')
    hips = Column(Float(asdecimal=True), nullable=False, server_default=text("0"), comment='Объем бедер (см)')
    bodyType_id = Column(INTEGER(11), comment='телосложение {rbBodyType}')
    bodyType = Column(String(20), comment='Телосложение')
    dailyVolume = Column(INTEGER(11), comment='Суточный объем физиологических отправлений')
    createPerson_id = Column(INTEGER(11), nullable=False, comment='Автор записи {Person}')
    modifyPerson_id = Column(INTEGER(11), nullable=False, comment='Автор изменения записи {Person}')
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')

    client = relationship('Client')


class SignedIEMKDocument(Base):
    __tablename__ = 'SignedIEMKDocument'
    __table_args__ = {'comment': 'Подписанные документы для ИЭМК'}

    id = Column(INTEGER(11), primary_key=True)
    client_id = Column(ForeignKey('Client.id', ondelete='CASCADE'), nullable=False)
    event_id = Column(INTEGER(11))
    action_id = Column(INTEGER(11))
    person_id = Column(INTEGER(11))
    sign_date = Column(DateTime)
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"))
    document_code = Column(String(20), nullable=False, server_default=text("''"))
    file_id = Column(INTEGER(11), nullable=False)
    sign_id = Column(INTEGER(11), nullable=False)
    html = Column(Text, nullable=False)
    template_id = Column(INTEGER(11), nullable=False)
    createPersonId = Column(INTEGER(11), nullable=False)
    status = Column(INTEGER(11), nullable=False, server_default=text("2"))
    description = Column(Text)
    messageId = Column(String(64))
    doc_date = Column(Date, nullable=False)
    doc_version = Column(INTEGER(11), nullable=False)
    mis_messageId = Column(String(64), nullable=False)
    local_uid = Column(Text)
    emdrId = Column(Text)
    notValidAfter = Column(DateTime, nullable=True)
    notValidBefore = Column(DateTime, nullable=True)
    certSerial = Column(String(128), nullable=True)
    certOwner = Column(String(512), nullable=True)
    file_path = Column(String(512), nullable=True)
    file_name = Column(String(512), nullable=True)
    ownerOrganisation = Column(String(512), nullable=True)
    txt = Column(Text, nullable=False)

    client = relationship('Client')


class IEMKSign(Base):
    __tablename__ = 'IEMKSign'
    __table_args__ = {'comment': 'Подписи SignedIEMKDocument'}

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(INTEGER(11), nullable=False)
    person_id = Column(INTEGER(11))
    signDateTime = Column(DateTime)
    formDateTime = Column(DateTime)
    file_path = Column(Text)
    file_name = Column(Text)
    sign_path = Column(Text)
    certOwner = Column(Text)
    certSerial = Column(Text)
    ownerOrganisation = Column(Text)
    notValidBefore = Column(DateTime)
    notValidAfter = Column(DateTime)
    deleted = Column(TINYINT(4), nullable=False, server_default=text("0"))


class IEMKStorage(Base):
    __tablename__ = 'IEMKStorage'
    __table_args__ = {'comment': 'Хранилище файлов ИЭМК'}

    id = Column(INTEGER(11), primary_key=True)
    path = Column(String(512))


class SignedREMDDocument(Base):
    __tablename__ = 'SignedREMDDocument'
    __table_args__ = {'comment': 'Документы для РЭМД'}

    id = Column(INTEGER(11), primary_key=True)
    createDateTime = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    status = Column(String(20), nullable=False, server_default=text("'error'"))
    MessageID = Column(String(64))
    RelatesTo = Column(String(64))
    data = Column(BLOB)
    checksum = Column(String(64))
    code = Column(String(64), server_default=text("''"))
    message = Column(String(64), server_default=text("''"))
    MisMessageId = Column(String(64))


class TempInvalidELN(Base):
    __tablename__ = 'TempInvalidELN'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"))
    duplicate = Column(TINYINT(1), nullable=False, server_default=text("0"))
    isImported = Column(TINYINT(1), nullable=False, server_default=text("0"))
    number = Column(String(16))
    prev_id = Column(INTEGER(11))
    prev_ln = Column(String(16))
    next_id = Column(INTEGER(11))
    next_ln = Column(String(16))
    lnDate = Column(Date)
    lpu_name = Column(String(90))
    lpu_address = Column(Text)
    lpu_ogrn = Column(String(15))
    caseDate = Column(Date)
    parent_id = Column(INTEGER(11))
    parent_ln = Column(String(16))
    client_id = Column(ForeignKey('Client.id'), ForeignKey('Client.id', ondelete='CASCADE', onupdate='CASCADE'))
    lastName = Column(String(60))
    firstName = Column(String(60))
    patrName = Column(String(60))
    birthDate = Column(Date)
    age = Column(TINYINT(1))
    sex = Column(TINYINT(1))
    SNILS = Column(String(11))
    isStationary = Column(TINYINT(1), nullable=False, server_default=text("0"))
    hospital_dt1 = Column(Date)
    hospital_dt2 = Column(Date)
    pregn12w_flag = Column(TINYINT(1), nullable=False, server_default=text("0"))
    reason1_id = Column(INTEGER(11))
    reason2_id = Column(ForeignKey('rbTempInvalidExtraReason.id'))
    diagnos = Column(String(10))
    mseDate1 = Column(Date)
    mseDate2 = Column(Date)
    mseDate3 = Column(Date)
    mse_invalid_group = Column(TINYINT(1))
    employerFlag = Column(TINYINT(1), nullable=False, server_default=text("0"))
    employer = Column(String(60))
    voucher_no = Column(String(10))
    voucher_ogrn = Column(String(15))
    date1 = Column(Date)
    date2 = Column(Date)
    serv1_lastname = Column(String(100))
    serv1_firstname = Column(String(100))
    serv1_patrname = Column(String(100))
    serv1_month = Column(INTEGER(3))
    serv1_age = Column(INTEGER(3))
    serv1_relation_code = Column(TINYINT(1))
    serv2_lastname = Column(String(60))
    serv2_firstname = Column(String(60))
    serv2_patrname = Column(String(60))
    serv2_month = Column(INTEGER(3))
    serv2_age = Column(INTEGER(3))
    serv2_relation_code = Column(TINYINT(1))
    letswork = Column(Date)
    breach_id = Column(ForeignKey('rbTempInvalidBreak.id'))
    breach_date = Column(Date)
    mse_result = Column(INTEGER(11))
    mse_date = Column(Date)
    begDate = Column(Date)
    endDate = Column(Date)
    duration = Column(INTEGER(4))
    person_id = Column(ForeignKey('Person.id'))
    note = Column(Text)
    closed = Column(TINYINT(1))
    state = Column(TINYINT(1))
    signedMessage = Column(Text)
    ln_hash = Column(String(32))
    serv1_fio = Column(String(100))
    serv2_fio = Column(String(100))
    reason3_id = Column(String(2))
    version = Column(String(12))
    unconditional = Column(TINYINT(1), nullable=False, server_default=text("0"))
    idMo = Column(String(60), server_default=text("''"))
    previouslyIssuedCode = Column(String(24), server_default=text("''"))
    writtenAgreementFlag = Column(TINYINT(1), nullable=False, server_default=text("1"))
    intermittenMethodFlag = Column(TINYINT(1), nullable=False, server_default=text("0"))
    serv1snils = Column(String(12), server_default=text("''"))
    isStatServ1 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    serv1birthday = Column(Date)
    serv1reason1 = Column(INTEGER(11))
    serv1diagnos = Column(String(10))
    chkCare1Serv1 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    chkCare2Serv1 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    chkCare3Serv1 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    edtBegCareDate1Serv1 = Column(Date)
    edtEndCareDate1Serv1 = Column(Date)
    edtBegCareDate2Serv1 = Column(Date)
    edtEndCareDate2Serv1 = Column(Date)
    edtBegCareDate3Serv1 = Column(Date)
    edtEndCareDate3Serv1 = Column(Date)
    serv2snils = Column(String(12), server_default=text("''"))
    isStatServ2 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    serv2birthday = Column(Date)
    serv2reason1 = Column(INTEGER(11))
    serv2diagnos = Column(String(10))
    chkCare1Serv2 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    chkCare2Serv2 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    chkCare3Serv2 = Column(TINYINT(1), nullable=False, server_default=text("0"))
    edtBegCareDate1Serv2 = Column(Date)
    edtEndCareDate1Serv2 = Column(Date)
    edtBegCareDate2Serv2 = Column(Date)
    edtEndCareDate2Serv2 = Column(Date)
    edtBegCareDate3Serv2 = Column(Date)
    edtEndCareDate3Serv2 = Column(Date)


class STREET(Base):
    __tablename__ = 'STREET'

    NAME = Column(String(40), nullable=False)
    SOCR = Column(String(10), nullable=False)
    CODE = Column(String(17), primary_key=True)
    INDEX = Column(String(6), nullable=False)
    GNINMB = Column(String(4), nullable=False)
    UNO = Column(String(4), nullable=False)
    OCATD = Column(String(11), nullable=False)
    infis = Column(String(5), nullable=False)


class DOMA(Base):
    __tablename__ = 'DOMA'

    NAME = Column(String(40), nullable=False)
    KORP = Column(String(10), nullable=False)
    SOCR = Column(String(10), nullable=False)
    CODE = Column(String(19), primary_key=True)
    INDEX = Column(String(6), nullable=False)
    GNINMB = Column(String(4), nullable=False)
    UNO = Column(String(4), nullable=False)
    OCATD = Column(String(11), nullable=False)
    flatHouseList = Column(Text, nullable=False)


class RbEGISZRegion(Base):
    __tablename__ = 'rbEGISZRegion'
    __table_args__ = {'comment': 'Субъекты Российской Федерации'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(16))
    name = Column(String(128))


class IEMKClientLog(Base):
    __tablename__ = 'IEMKClientLog'
    __table_args__ = {'comment': 'Лог отправки данных о клиенте в ИЭМК'}

    id = Column(INTEGER(11), primary_key=True)
    client_id = Column(INTEGER(11), nullable=False)
    sendDate = Column(DateTime)
    status = Column(TINYINT(5), server_default=text("1"))
    error_code = Column(TINYINT(4), nullable=False, server_default=text("0"))
    error_message = Column(Text)


class IEMKEventLog(Base):
    __tablename__ = 'IEMKEventLog'
    __table_args__ = {
        'comment': 'Лог отправки данных о слеучае лечения в ИЭМК. Записи со статусом 0 попадают сюда, когда Eventу проставляют execDate'}

    id = Column(INTEGER(11), primary_key=True)
    event_id = Column(INTEGER(11), nullable=False)
    sendDate = Column(DateTime)
    status = Column(TINYINT(5), server_default=text("0"))
    error_code = Column(TINYINT(4), nullable=False, server_default=text("0"))
    error_message = Column(Text)
    method = Column(String(32))
    action_id = Column(INTEGER(11))
    diagnosis_id = Column(INTEGER(11))
    client_id = Column(INTEGER(11))
    createDateTime = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))


class ActionPropertyDate(Base):
    __tablename__ = 'ActionProperty_Date'
    __table_args__ = {'comment': 'Значение свойства действия'}

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False)
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"))
    value = Column(Date)


class ActionPropertyDateTime(Base):
    __tablename__ = 'ActionProperty_DateTime'
    __table_args__ = {'comment': 'Значение свойства действия'}

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False)
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"))
    value = Column(DateTime)


class ActionPropertyDouble(Base):
    __tablename__ = 'ActionProperty_Double'
    __table_args__ = {'comment': 'Значение свойства действия'}

    id = Column(ForeignKey('ActionProperty.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                nullable=False)
    index = Column(INTEGER(11), primary_key=True, nullable=False, server_default=text("0"))
    value = Column(Float(asdecimal=True), nullable=False)


class NSIRefBook(Base):
    __tablename__ = 'NSIRefBooks'
    __table_args__ = {'comment': 'Список справочников НСИ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(Text)
    name = Column(INTEGER(11))
    OID = Column(Text)
    version = Column(String(10))
    reference = Column(Text)


class RbDisabilityGroup(Base):
    __tablename__ = 'rbDisabilityGroup'
    __table_args__ = {'comment': 'Группы инвалидности - справочник: 1.2.643.5.1.13.13.11.1053'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(8), nullable=False)
    name = Column(String(64), nullable=False)
    displayName = Column(Text)


class RbMSECitizenship(Base):
    __tablename__ = 'rbMSECitizenship'
    __table_args__ = {'comment': 'Гражданство при направлении на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEClientBodyType(Base):
    __tablename__ = 'rbMSEClientBodyType'
    __table_args__ = {'comment': 'Типы телосложения'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEClientEducationLevel(Base):
    __tablename__ = 'rbMSEClientEducationLevel'
    __table_args__ = {'comment': 'Уровень образования'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEClientLocOrg(Base):
    __tablename__ = 'rbMSEClientLocOrg'
    __table_args__ = {'comment': 'Местонахождение гражданина при направлении на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEClinicalPredict(Base):
    __tablename__ = 'rbMSEClinicalPredict'
    __table_args__ = {'comment': 'Клинический прогноз'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDisabilityPrimary(Base):
    __tablename__ = 'rbMSEDisabilityPrimary'
    __table_args__ = {'comment': 'Тип установления инвалидности'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDisabledDate(Base):
    __tablename__ = 'rbMSEDisabledDate'
    __table_args__ = {'comment': 'Срок, на который установлена инвалидность'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDisabledPeriod(Base):
    __tablename__ = 'rbMSEDisabledPeriod'
    __table_args__ = {'comment': 'Период инвалидности'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMseRepeat(Base):
    __tablename__ = 'referral_mse_repeat'
    __table_args__ = {'comment': 'Период инвалидности'}
    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(INTEGER(11))
    date_invalid = Column(DateTime, nullable=False)
    invalid = Column(VARCHAR(64))
    invalid_period = Column(VARCHAR(64))
    invalid_reason = Column(VARCHAR(200))
    invalid_missing = Column(VARCHAR(64))
    invalid_time = Column(VARCHAR(64))
    invalid_date = Column(DateTime, nullable=False)
    invalid_grade = Column(VARCHAR(64))
    invalid_kind = Column(INTEGER(11))
    deleted = Column(TINYINT(4))
    disabled_date = Column(INTEGER(11))


class RbMSEDisabledReason(Base):
    __tablename__ = 'rbMSEDisabledReason'
    __table_args__ = {'comment': 'Причины инвалидности'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDisabledWorkDate(Base):
    __tablename__ = 'rbMSEDisabledWorkDate'
    __table_args__ = {'comment': 'Срок, на который установлена степень утраты профессиональной трудоспособности'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDocumentType(Base):
    __tablename__ = 'rbMSEDocumentType'
    __table_args__ = {'comment': 'Документы, удостоверяющие личность при направлении на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEGoal(Base):
    __tablename__ = 'rbMSEGoal'
    __table_args__ = {'comment': 'Цели направления на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEMilitaryStatu(Base):
    __tablename__ = 'rbMSEMilitaryStatus'
    __table_args__ = {'comment': 'Воинская обязанность при направлении на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEPrimary(Base):
    __tablename__ = 'rbMSEPrimary'
    __table_args__ = {'comment': 'Порядок обращения на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSERehabilitationPotential(Base):
    __tablename__ = 'rbMSERehabilitationPotential'
    __table_args__ = {'comment': 'Реабилитационный потенциал'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSERehabilitationPredict(Base):
    __tablename__ = 'rbMSERehabilitationPredict'
    __table_args__ = {'comment': 'Реабилитационный прогноз'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEReprAuthority(Base):
    __tablename__ = 'rbMSEReprAuthority'
    __table_args__ = {'comment': 'Документы удостоверяющие полномочия представителя'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSESex(Base):
    __tablename__ = 'rbMSESex'
    __table_args__ = {'comment': 'Пол пациента при направлении на МСЭ'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDiagnosisType(Base):
    __tablename__ = 'rbMSEDiagnosisType'
    __table_args__ = {'comment': 'Степень обоснованности диагноза'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSERehResult(Base):
    __tablename__ = 'rbMSERehResults'
    __table_args__ = {'comment': 'Результаты индивидуальной программы реабилитации инвалидов'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(INTEGER(11))
    name = Column(Text)
    displayName = Column(Text)


class RbMSEDiagnostic(Base):
    __tablename__ = 'rbMSEDiagnostic'
    __table_args__ = {
        'comment': 'Медицинские обследования для медико-социальной экспертизы {1.2.643.5.1.13.13.99.2.857}'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(Text)
    mkb = Column(Text)
    nmu = Column(Text)
    name = Column(Text)
    date = Column(Text)
    is_primary = Column(INTEGER(11))
    section = Column(INTEGER(11))


class RbMSEMedication(Base):
    __tablename__ = 'rbMSEMedication'
    __table_args__ = {'comment': '1.2.643.5.1.13.13.99.2.611'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(250))
    name = Column(Text)
    form = Column(String(150))


class RbResult(Base):
    __tablename__ = 'rbResult'
    __table_args__ = {'comment': 'Результат обращения'}

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    eventPurpose_id = Column(ForeignKey('rbEventTypePurpose.id'), nullable=False)
    code = Column(String(8), nullable=False)
    name = Column(String(255), nullable=False)
    continued = Column(TINYINT(1), nullable=False)
    regionalCode = Column(String(8), nullable=False)
    federalCode = Column(String(8), nullable=False)
    notAccount = Column(TINYINT(1), nullable=False, server_default=text("0"))
    counter_id = Column(ForeignKey('rbCounter.id'))
    begDate = Column(Date, nullable=False, server_default=text("'1900-01-01'"))
    endDate = Column(Date, nullable=False, server_default=text("'2999-12-31'"))
    attachType = Column(ForeignKey('rbAttachType.id', ondelete='SET NULL', onupdate='CASCADE'))
    socStatusClass = Column(ForeignKey('rbSocStatusClass.id', ondelete='SET NULL', onupdate='CASCADE'))
    socStatusType = Column(ForeignKey('rbSocStatusType.id', ondelete='SET NULL', onupdate='CASCADE'))
    isDeath = Column(TINYINT(1), nullable=False, server_default=text("0"))
    netrica_Code = Column(String(65))
    caseCast_id = Column(INTEGER(11))

    rbAttachType = relationship('RbAttachType')
    counter = relationship('RbCounter')
    createPerson = relationship('Person', primaryjoin='RbResult.createPerson_id == Person.id')
    eventPurpose = relationship('RbEventTypePurpose')
    modifyPerson = relationship('Person', primaryjoin='RbResult.modifyPerson_id == Person.id')
    rbSocStatusClass = relationship('RbSocStatusClass')
    rbSocStatusType = relationship('RbSocStatusType')


class GetStatusTable(Base):
    __tablename__ = 'GetStatusTable'
    __table_args__ = {'comment': ' Лог данных из шин'}

    id = Column(INTEGER(11), primary_key=True)
    event_id = Column(INTEGER(16), nullable=False)
    action_id = Column(INTEGER(16), nullable=True)
    status_semd = Column(TINYINT(1), nullable=False)
    client_id = Column(INTEGER(16), nullable=False)
    person_id = Column(INTEGER(16), nullable=True)
    semd_name = Column(String(1024), nullable=True)
    error_description = Column(String(1024), nullable=True)
    template_id = Column(INTEGER(16), nullable=True)
    remd_id = Column(String(1024), nullable=True)
    result_remd = Column(String(1024), nullable=True)
    remd_status = Column(TINYINT(1), nullable=True)
    date_create = Column(String(1024), nullable=True)
    date_accept = Column(String(1024), nullable=True)
    sign = Column(TINYINT(1), nullable=True)
    sign_mo = Column(TINYINT(1), nullable=True)
    doc_oid = Column(String(128), nullable=True)
    semd_code = Column(String(128), nullable=True)
    iemk_doc = Column(TINYINT(1), default=0, nullable=False)
    iemk_status = Column(TINYINT(1), default=0, nullable=False)
    iemk_error = Column(String(128), nullable=True)
    sign_iemk = Column(TINYINT(1), default=0, nullable=False)
    sign_iemk_mo = Column(TINYINT(1), default=0, nullable=False)
    date_start = Column(Date)


class GetStatusTable2(Base):
    __tablename__ = 'GetStatusTable2'
    __table_args__ = {'comment': ' Лог данных из шин'}

    id = Column(INTEGER(11), primary_key=True)
    event_id = Column(INTEGER(16), nullable=False)
    action_id = Column(INTEGER(16), nullable=True)
    status_semd = Column(TINYINT(1), nullable=False)
    client_id = Column(INTEGER(16), nullable=False)
    person_id = Column(INTEGER(16), nullable=True)
    semd_name = Column(String(1024), nullable=True)
    error_description = Column(String(1024), nullable=True)
    template_id = Column(INTEGER(16), nullable=True)
    remd_id = Column(String(1024), nullable=True)
    result_remd = Column(String(1024), nullable=True)
    remd_status = Column(TINYINT(1), nullable=True)
    date_create = Column(String(1024), nullable=True)
    date_accept = Column(String(1024), nullable=True)
    sign = Column(TINYINT(1), nullable=True)
    sign_mo = Column(TINYINT(1), nullable=True)
    doc_oid = Column(String(128), nullable=True)
    semd_code = Column(String(128), nullable=True)
    iemk_doc = Column(TINYINT(1), default=0, nullable=False)
    iemk_status = Column(TINYINT(1), default=0, nullable=False)
    iemk_error = Column(String(128), nullable=True)
    sign_iemk = Column(TINYINT(1), default=0, nullable=False)
    sign_iemk_mo = Column(TINYINT(1), default=0, nullable=False)
    date_start = Column(Date)

class RbIEMKDocument(Base):
    __tablename__ = 'rbIEMKDocument'
    __table_args__ = {'comment': 'Справочник посылаемых документов ИЭМК'}

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    EGISZ_code = Column(INTEGER(11))
    SEMD_code = Column(INTEGER(11))
    mark = Column(TINYINT(1))
    netrica_Code = Column(String(128), nullable=False)
    type = Column(String(64), nullable=True)


class ReferralMse(Base):
    __tablename__ = 'referral_mse'

    id = Column(INTEGER(11), primary_key=True)
    fio = Column(String(300))
    age = Column(INTEGER(11))
    birthDate = Column(DateTime)
    sex = Column(INTEGER(2))
    citizenship = Column(INTEGER(100))
    militaryStatus = Column(INTEGER(200))
    addressCountry = Column(String(200))
    addressArea = Column(String(200))
    addressCity = Column(String(200))
    addressSubject = Column(String(200))
    addressHouse = Column(String(100))
    addressCorpus = Column(String(50))
    addressLitera = Column(String(10))
    addressFlat = Column(String(50))
    addressIndex = Column(String(10))
    addressBOMJ = Column(TINYINT(1), server_default=text("0"))
    locationOrg = Column(INTEGER(11))
    locationOGRN = Column(String(20))
    locationAddr = Column(String(300))
    contactPhone = Column(String(20))
    contactEmail = Column(String(100))
    client_id = Column(INTEGER(11))
    documentSNILS = Column(String(15))
    documentType = Column(String(20))
    documentSerial = Column(String(10))
    documentNumber = Column(String(20))
    documentInsWho = Column(String(300))
    documentInsDate = Column(Date)
    isRepresentative = Column(TINYINT(4))
    representativeFIO = Column(String(300))
    representativeBirthDate = Column(Date)
    representativeUdDocumentType = Column(String(100))
    representativeUdDocumentNumber = Column(String(50))
    representativeUdDocumentSerial = Column(String(10))
    representativeUdDocumentInsWho = Column(String(300))
    representativeUdDocumentInsDate = Column(Date)
    representativeDocumentType = Column(String(100))
    representativeDocumentSerial = Column(String(10))
    representativeDocumentNumber = Column(String(50))
    representativeDocumentInsDate = Column(Date)
    representativeDocumentInsWho = Column(String(300))
    representativeContactsPhone = Column(String(100))
    representativeContactsEmail = Column(String(100))
    representativeContactsSNILS = Column(String(50))
    representativeOrgName = Column(String(300))
    representativeOrgAddress = Column(String(300))
    representativeOrgOGRN = Column(String(50))
    isEducation = Column(TINYINT(4))
    educationOrgName = Column(String(300))
    educationOrgAddress = Column(String(300))
    educationLevel = Column(String(50))
    educationLevelVal = Column(String(50))
    educationSpeciality = Column(String(100))
    isWorking = Column(TINYINT(4))
    workingOrgName = Column(String(300))
    workingOrgAddress = Column(String(300))
    workingSpeciality = Column(String(300))
    workingQualification = Column(String(100))
    workingExp = Column(INTEGER(11))
    workingCharacter = Column(String(300))
    protocolNumber = Column(String(100))
    protocolDate = Column(Date)
    protocolReferralDate = Column(Date)
    protocolReferralGoal = Column(String(50))
    otherGoals = Column(String(300))
    mseAtHome = Column(TINYINT(4))
    pallatativeMedicalCare = Column(TINYINT(4))
    anamnesisWeight = Column(String(10))
    anamnesisIndex = Column(String(10))
    anamnesisHeight = Column(String(10))
    anamnesisBodyType = Column(INTEGER(11))
    anamnesisHips = Column(String(30))
    anamnesisWaist = Column(String(30))
    anamnesisDailyVal = Column(String(30))
    anamnesisPhysics = Column(String(50))
    anamnesisChildWeight = Column(String(10))
    primaryMSE = Column(INTEGER(11))
    isPrevMSE = Column(TINYINT(4))
    prevMSEresults = Column(String(300))
    isVUT = Column(TINYINT(4))
    VUTresults = Column(String(300))
    clinicMedOrganisation = Column(String(100))
    clinicSickList = Column(MEDIUMTEXT)
    clinicAnamnesisVitae = Column(MEDIUMTEXT)
    clinicClientCondition = Column(MEDIUMTEXT)
    clinicDiagnosticInfo = Column(MEDIUMTEXT)
    clinisDiagnosis = Column(String(300))
    clinicClinicalPrediction = Column(String(100))
    clinicReaPrediction = Column(String(50))
    clinicReaPotential = Column(String(50))
    clinicRecommendationsReabilitation = Column(MEDIUMTEXT)
    clinicRecommendationsRecSurgery = Column(MEDIUMTEXT)
    clinicRecommendationsProtes = Column(MEDIUMTEXT)
    clinicHealthResTreatment = Column(MEDIUMTEXT)
    result = Column(String(200))
    send_in_iemk = Column(TINYINT(4), nullable=False, server_default=text("0"))
    event_id = Column(INTEGER(11))
    firstName = Column(String(100))
    lastName = Column(String(100))
    patrName = Column(String(100))
    addressStreet = Column(String(100))
    documentType_code = Column(String(16))
    signedByPerson = Column(TINYINT(1), server_default=text("0"))
    signedByMO = Column(TINYINT(1), server_default=text("0"))
    org_id = Column(INTEGER(11))
    rec_org_id = Column(INTEGER(11))
    result_achievement = Column(INTEGER(11))
    result_number = Column(String(30))
    result_mse_number = Column(String(30))
    result_date = Column(Date)
    result_text = Column(String(500))
    person_id = Column(INTEGER(11))
    REMDMsg = Column(Text)
    REMDStatus = Column(String(40))
    REMDId = Column(String(20))
    deleted = Column(TINYINT(1), nullable=False, server_default=text("0"))
    work = Column(Text)
    otherContactPhone = Column(String(20))
    elnNumber = Column(String(20))
    remd_status = Column(String(128), server_default=text("''"))
    locationAddrKLADR = Column(String(64))
    representativeOrgAddressKLADR = Column(String(64))
    workingOrgAddressKLADR = Column(String(64))
    special_care = Column(MEDIUMTEXT)
    medical_devices = Column(MEDIUMTEXT)
    client_complaints = Column(MEDIUMTEXT)
    client_policy = Column(String(20))
    invalid = Column(INTEGER(11))
    invalid_kind = Column(INTEGER(11))
    disabled_date = Column(INTEGER(11))
    invalid_period = Column(INTEGER(11))
    invalid_reason = Column(INTEGER(11))
    date_invalid = Column(Date)
    need_protesis = Column(INTEGER(11))
    consent_date = Column(DateTime)
    preferred_form = Column(INTEGER(11))
    receiving_notification_methods = Column(String(128))
    version_mse = Column(TINYINT(1))


class RbPrerecordQuotaType(Base):
    __tablename__ = 'rbPrerecordQuotaType'
    __table_args__ = {'comment': 'Тип квот для предварительной записи'}

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False)
    createPerson_id = Column(ForeignKey('Person.id'))
    modifyDatetime = Column(DateTime, nullable=False)
    modifyPerson_id = Column(ForeignKey('Person.id'))
    code = Column(String(16), nullable=False)
    name = Column(String(64), nullable=False)
    defaultValue = Column(SMALLINT(4), nullable=False, server_default=text("0"))

    createPerson = relationship('Person', primaryjoin='RbPrerecordQuotaType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbPrerecordQuotaType.modifyPerson_id == Person.id')


class PersonPrerecordQuota(Base):
    __tablename__ = 'PersonPrerecordQuota'
    __table_args__ = {'comment': 'Значения квот предварительной записи для каждого работника'}

    id = Column(INTEGER(11), primary_key=True)
    person_id = Column(ForeignKey('Person.id', ondelete='CASCADE'), nullable=False)
    quotaType_id = Column(ForeignKey('rbPrerecordQuotaType.id', ondelete='CASCADE'), nullable=False)
    value = Column(SMALLINT(4), nullable=False)

    person = relationship('Person')
    quotaType = relationship('RbPrerecordQuotaType')


class Referral(Base):
    __tablename__ = 'Referral'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, nullable=False, comment='Дата создания записи')
    createPerson_id = Column(INTEGER(11), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, nullable=False, comment='Дата изменения записи')
    modifyPerson_id = Column(INTEGER(11), comment='Автор изменения записи {Person}')
    deleted = Column(TINYINT(1), nullable=False, comment='Отметка удаления записи')
    number = Column(String(30), nullable=False, comment='Номер направления')
    recid = Column(INTEGER(11), comment='Идентификатор записи в БД ЦОДа')
    status = Column(String(64), comment='Cтатус обработки заявки')
    client_id = Column(INTEGER(11), nullable=False, comment='Пациент {Client}')
    event_id = Column(INTEGER(11), comment='Идетификатор события {Event}')
    policy_id = Column(INTEGER(11), comment='Полис пациента привязаный к направлению {ClientPolicy}')
    doc_id = Column(INTEGER(11), comment='Документ(паспорт) пациента привязаный к направлению {ClientDocument}')
    date = Column(DateTime, nullable=False, comment='Дата выдачи направления')
    execDate = Column(DateTime, comment='Дата начала выполнения направления')
    startDate = Column(DateTime, comment='Дата начала действия направления')
    endDate = Column(DateTime, comment='Дата окончания действия направления')
    hospDate = Column(Date, comment='Плановая дата госпитализации')
    relegateOrg_id = Column(INTEGER(11), comment='Направитель {Organisation}')
    freeInput = Column(String(80), comment='Альтернатива - свободный ввод')
    person = Column(String(80), comment='Имя направившего врача')
    speciality_id = Column(INTEGER(11), comment='Специальность направившего врача {rbSpeciality}')
    MKB = Column(String(8), comment='МКБ код диагноза')
    type = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='Тип направления (0-ЛПУ, 1-военкомат)')
    hospBedProfile_id = Column(INTEGER(11))
    actionTypeCode = Column(String(32), comment='Код типа действия')
    isCancelled = Column(TINYINT(1), server_default=text("0"), comment='Признак анулирования направления')
    cancelPerson_id = Column(INTEGER(11), comment='Идентификатор аннулировавшего направление {Person}')
    cancelDate = Column(DateTime, comment='Дата аннулирования направления')
    cancelReason = Column(INTEGER(11), comment='Причина аннулирования {rbCancellationReason}')
    notes = Column(Text, comment='Комментарий к направлению')
    rationale = Column(Text, comment='Обоснование')
    patientCondition = Column(Text, comment='Состояние пациента')
    netrica_id = Column(Text, comment='Идентификатор направления в справочнике Нетрики')
    approved = Column(TINYINT(1), comment='Признак подтверждения')
    isSend = Column(TINYINT(1), server_default=text("0"),
                    comment='Признак отправленного направления {0 - полученое, 1 - отправленое}')
    medProfile_id = Column(INTEGER(11), comment='Профиль медицинской помощи {rbMedicalAidProfile}')
    orgStructure = Column(INTEGER(11), comment='Профиль отделения {rbOrgStructureProfile}')
    clinicType = Column(INTEGER(3), comment='Тип стационара 1 - Стационар 2 - Дневной стационар')
    ticketNumber = Column(Text)
    isHospitalized = Column(TINYINT(1), server_default=text("0"), comment='Признак госпитализации пациента целевым МО')
    relMoHospDate = Column(Date, comment='Дата госпитализации целевым МО')
    examType = Column(INTEGER(11), server_default=text("0"), comment='Вид назначенного обследования')
    organ = Column(INTEGER(11), server_default=text("0"), comment='Орган назначенного обследования')
    hospitalisationType = Column(TINYINT(4), comment='Тип госпитализации(0-экстренная, 1-плановая)')
    regionalGuide_id = Column(INTEGER(11), comment='Региональный направитель. rbOrganisation')
    relegateOrgTo_id = Column(INTEGER(11), comment='id организации, куда пациент был направлен')
    goalType = Column(INTEGER(11), comment='Тип цели (Справочник SPRAV_GOAL_TYPE2 {rbGoalType2}')
    action_id = Column(INTEGER(11), comment='для ТМ')
    canEdit = Column(TINYINT(1), server_default=text("0"),
                     comment='Если напрваление создано в обращении во вкладке доп. данных то его можно редактировать')


class RbReferralType(Base):
    __tablename__ = 'rbReferralType'

    id = Column(INTEGER(11), primary_key=True)
    createDatetime = Column(DateTime, server_default=text("current_timestamp()"), comment='Дата добавления')
    createPerson_id = Column(ForeignKey('Person.id'), comment='Автор записи {Person}')
    modifyDatetime = Column(DateTime, comment='Дата редактирования')
    modifyPerson_id = Column(ForeignKey('Person.id'), comment='Автор изменения {Person}')
    code = Column(String(32), nullable=False, comment='Код')
    name = Column(String(64), nullable=False, comment='Наименование')
    netrica_Code = Column(String(6), comment='Код в справочнике Нетрики')
    EGISZ_code = Column(String(16))

    createPerson = relationship('Person', primaryjoin='RbReferralType.createPerson_id == Person.id')
    modifyPerson = relationship('Person', primaryjoin='RbReferralType.modifyPerson_id == Person.id')


class RbAcceptanceStatus(Base):
    __tablename__ = 'rbAcceptanceStatus'

    id = Column(INTEGER(11), primary_key=True)
    code = Column(String(255))
    name = Column(String(50))


class TicketDms(Base):
    __tablename__ = 'TicketDms'

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(ForeignKey('Action.id', ondelete='CASCADE'), nullable=False, comment='Номерок {Action}')
    org_id = Column(ForeignKey('Organisation.id', ondelete='SET NULL'), comment='ДМС компания {Organisation}')
    representative_name = Column(String(128), comment='Имя представителя')
    mkb = Column(String(16), comment='Код диагноза по МКБ-10')
    operator_id = Column(ForeignKey('Person.id', ondelete='SET NULL'), comment='Оператор {Person}')
    note = Column(String(256), comment='Комментарии')

    master = relationship('Action')
    operator = relationship('Person')
    org = relationship('Organisation')


class TicketInfo(Base):
    __tablename__ = 'TicketInfo'

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(ForeignKey('Action.id', ondelete='CASCADE'), nullable=False, comment='Номерок {Action}')
    queueStatus_id = Column(ForeignKey('rbAcceptanceStatus.id', ondelete='SET NULL'),
                            comment='Статус приема пациента {rbAcceptanceStatus}')
    client_name = Column(String(128), comment='Имя пациента (для предзаписи)')
    moved_from_ticket = Column(String(128), comment='Время, с которого перенесён номерок')
    moved_by_user = Column(String(128), comment='Пользователь, который перенёс номерок')
    moved_from_person = Column(String(128), comment='Врач, с которого перенесён номерок')

    master = relationship('Action')
    queueStatus = relationship('RbAcceptanceStatus')


class TicketService(Base):
    __tablename__ = 'Ticket_Service'

    id = Column(INTEGER(11), primary_key=True)
    master_id = Column(ForeignKey('Action.id', ondelete='CASCADE'), nullable=False, comment='Номерок {Action}')
    service_id = Column(ForeignKey('rbService.id', ondelete='SET NULL'), comment='Услуга {rbService}')

    master = relationship('Action')
    service = relationship('RbService')


class MSEPreferredForm(Base):
    __tablename__ = 'medical_and_social_expertise_preferred_form'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(50))
    name_088_488_551 = Column(String(50))
    code = Column(INTEGER(11))


class MSEReceivingNotificationMethod(Base):
    __tablename__ = 'medical_and_social_expertise_receiving_notification_method'

    id = Column(INTEGER(11), primary_key=True)
    notification = Column(String(256))
    code = Column(INTEGER(11))
    name = Column(Text)


class Rbdiagnosisnosologytype(Base):
    __tablename__ = 'rbDiagnosisNosologyType'

    id = Column(INTEGER(11), primary_key=True)
    egisz_code = Column(String(8), comment='1.2.643.5.1.13.13.11.1077')
    FULL_NAME = Column(Text)
    SHORT_NAME = Column(String(64))
    name = Column(String(255))
    code = Column(INTEGER(11))


class SlotLock(Base):
    __tablename__ = 'SlotLock'

    id = Column(INTEGER(11), primary_key=True)
    slot = Column(String(32), nullable=False, comment='Слот расписания')
    person_id = Column(ForeignKey('Person.id', ondelete='CASCADE'), nullable=False,
                       comment='Заблокировавший пользователь {Person}')
    lock_time = Column(DateTime, nullable=False, comment='Время блокировки')
    release_time = Column(DateTime, comment='Время снятия блокировки')

    person = relationship('Person')


def isBase(object):
    if inspect.isclass(object) and issubclass(object, Base):
        if hasattr(object, "__tablename__"):
            return True
    return False


clsmembers = inspect.getmembers(sys.modules[__name__], isBase)
