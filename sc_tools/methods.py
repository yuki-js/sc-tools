"""Usable methods for Smart Cards"""

from enum import Flag
from tqdm import tqdm
from typing import Callable

from .apdu import CommandApdu
from .card_response import CardResponseStatusType, CardResponseError
from .card_connection import CardConnection


class CardFileAttribute(Flag):
    UNKNOWN = 0x00000000
    WEF_TRANSPARENT = 0x00000001
    WEF_RECORD = 0x00000002
    IEF_VERIFY_KEY = 0x00000010
    IEF_INTERNAL_AUTHENTICATE_KEY = 0x00000020
    IEF_EXTERNAL_AUTHENTICATE_KEY = 0x00000040
    LOCKED = 0x00000100
    VERIFICATION_REQUIRED = 0x00000200
    VERIFICATION_UNLIMITED = 0x00000400
    JPKI_SIGN_PRIVATE_KEY = 0x00001000


def list_cla_ins(
    connection: CardConnection,
    cla_start: int = 0x00,
    cla_end: int = 0x100,
    ins_start: int = 0x00,
    ins_end: int = 0x100,
) -> list[tuple[int, int, CardResponseStatusType]]:
    """List valid CLA-INS

    Args:
        connection (CardConnection): Card Connection
        cla_start (int, optional): CLA start. Defaults to 0x00.
        cla_end (int, optional): CLA end. Defaults to 0x100.
        ins_start (int, optional): INS start. Defaults to 0x00.
        ins_end (int, optional): INS end. Defaults to 0x100.

    Raises:
        ValueError: Invalid argument `cla_start`
        ValueError: Invalid argument `cla_end`
        ValueError: Invalid argument `ins_start`
        ValueError: Invalid argument `ins_end`

    Returns:
        list[tuple[int, int, CardResponseStatusType]]: List of valid CLA-INS and Response Status
    """

    if cla_start < 0x00 or 0x100 < cla_start:
        raise ValueError(
            "Argument `cla_start` out of range. (0x00 <= cla_start <= 0x100)"
        )
    if cla_end < 0x00 or 0x100 < cla_end:
        raise ValueError("Argument `cla_end` out of range. (0x00 <= cla_end <= 0x100)")
    if ins_start < 0x00 or 0x100 < ins_start:
        raise ValueError(
            "Argument `ins_start` out of range. (0x00 <= ins_start <= 0x100)"
        )
    if ins_end < 0x00 or 0x100 < ins_end:
        raise ValueError("Argument `ins_end` out of range. (0x00 <= ins_end <= 0x100)")

    cla_ins_list: list[tuple[int, int, CardResponseStatusType]] = []
    for cla in tqdm(range(cla_start, cla_end), desc="List valid CLA-INS"):
        for ins in range(ins_start, ins_end):
            command = CommandApdu(
                cla, ins, 0x00, 0x00, extended=connection.allow_extended_apdu
            )
            status, data = connection.transmit(command, raise_error=False)
            status_type = status.status_type()
            if status_type == CardResponseStatusType.CLASS_NOT_PROVIDED:
                break
            if (
                status_type == CardResponseStatusType.INS_NOT_PROVIDED
                or status_type
                == CardResponseStatusType.ACCESS_FEATURE_WITH_THE_SPECIFIED_LOGICAL_CHANNEL_NUMBER_NOT_PROVIDED
                or status_type
                == CardResponseStatusType.SECURE_MESSAGING_FEATURE_NOT_PROVIDED
            ):
                continue
            cla_hex = format(cla, "02X")
            ins_hex = format(ins, "02X")
            sw_hex = format(status.sw, "04X")
            tqdm.write(
                f"CLA {cla_hex}, INS {ins_hex} found with status {sw_hex} ({status_type})."
            )
            cla_ins_list.append((cla, ins, status))
    return cla_ins_list


def list_p1_p2(
    connection: CardConnection,
    cla: int,
    ins: int,
    p1_start: int = 0x00,
    p1_end: int = 0x100,
    p2_start: int = 0x00,
    p2_end: int = 0x100,
) -> list[tuple[int, int, CardResponseStatusType]]:
    """List valid P1-P2

    Args:
        connection (CardConnection): Card Connection
        cla (int): CLA
        ins (int): INS
        p1_start (int, optional): P1 start. Defaults to 0x00.
        p1_end (int, optional): P1 end. Defaults to 0x100.
        p2_start (int, optional): P2 start. Defaults to 0x00.
        p2_end (int, optional): P2 end. Defaults to 0x100.

    Raises:
        ValueError: Invalid argument `cla`
        ValueError: Invalid argument `ins`
        ValueError: Invalid argument `p1_start`
        ValueError: Invalid argument `p1_end`
        ValueError: Invalid argument `p2_start`
        ValueError: Invalid argument `p2_end`

    Returns:
        list[tuple[int, int, CardResponseStatusType]]: List of valid P1-P2 and Response Status
    """

    if cla < 0x00 or 0xFF < cla:
        raise ValueError("Argument `cla` out of range. (0x00 <= cla <= 0xFF)")
    if ins < 0x00 or 0xFF < ins:
        raise ValueError("Argument `ins` out of range. (0x00 <= ins <= 0xFF)")
    if p1_start < 0x00 or 0x100 < p1_start:
        raise ValueError(
            "Argument `p1_start` out of range. (0x00 <= p1_start <= 0x100)"
        )
    if p1_end < 0x00 or 0x100 < p1_end:
        raise ValueError("Argument `p1_end` out of range. (0x00 <= p1_end <= 0x100)")
    if p2_start < 0x00 or 0x100 < p2_start:
        raise ValueError(
            "Argument `p2_start` out of range. (0x00 <= p2_start <= 0x100)"
        )
    if p2_end < 0x00 or 0x100 < p2_end:
        raise ValueError("Argument `p2_end` out of range. (0x00 <= p2_end <= 0x100)")

    p1_p2_list: list[tuple[bytes, CardResponseStatusType]] = []
    for p1 in tqdm(range(p1_start, p1_end), desc="List valid P1-P2"):
        for p2 in range(p2_start, p2_end):
            # No Le
            command = CommandApdu(
                cla, ins, p1, p2, extended=connection.allow_extended_apdu
            )
            status, data = connection.transmit(command, raise_error=False)
            status_type = status.status_type()
            if status_type != CardResponseStatusType.INCORRECT_P1_P2_VALUE:
                p1_hex = format(p1, "02X")
                p2_hex = format(p2, "02X")
                sw_hex = format(status.sw, "04X")
                tqdm.write(
                    f"P1 {p1_hex}, P2 {p2_hex}, No Le found with status {sw_hex} ({status_type})."
                )
                p1_p2_list.append((p1, p2, status))
                continue
            # Le=MAX
            command.le = "max"
            status, data = connection.transmit(command, raise_error=False)
            status_type = status.status_type()
            if status_type != CardResponseStatusType.INCORRECT_P1_P2_VALUE:
                p1_hex = format(p1, "02X")
                p2_hex = format(p2, "02X")
                sw_hex = format(status.sw, "04X")
                tqdm.write(
                    f"P1 {p1_hex}, P2 {p2_hex}, Le=MAX found with status {sw_hex} ({status_type})."
                )
                p1_p2_list.append((p1, p2, status))
                continue
    return p1_p2_list


def attribute_ef(
    connection: CardConnection,
    ef_id: bytes,
    cla: int = 0x00,
) -> CardFileAttribute:
    """Attribute EF

    Args:
        connection (CardConnection): Card Connection
        ef_id (bytes): EF identifier
        cla (int, optional): CLA. Defaults to 0x00.

    Raises:
        ValueError: Invalid argument `ef_id`
        ValueError: Invalid argument `cla`

    Returns:
        CardFileAttribute: EF Attribute
    """

    if len(ef_id) != 2:
        raise ValueError("Argument `ef_id` length must be 2.")
    if cla < 0x00 or 0xFF < cla:
        raise ValueError("Argument `cla` out of range. (0x00 <= cla <= 0xFF)")

    status, data = connection.select_ef(ef_id, cla=cla)

    ef_attribute = CardFileAttribute.UNKNOWN

    # IEF/VERIFY_KEY
    status, data = connection.verify(None, cla=cla, raise_error=False)
    status_type = status.status_type()
    if status_type == CardResponseStatusType.VERIFICATION_UNMATCHING:
        ef_attribute = CardFileAttribute.IEF_VERIFY_KEY
        if status.verification_remaining() is None:
            ef_attribute |= CardFileAttribute.VERIFICATION_UNLIMITED
        if status.verification_remaining() == 0:
            ef_attribute |= CardFileAttribute.LOCKED
        return ef_attribute

    # # IEF/INTERNAL_AUTHENTICATE_KEY
    # status, data = connection.internal_authenticate(
    #     b"\x00", cla, raise_error=False
    # )
    # status_type = status.status_type()
    # if status_type == CardResponseStatusType.VERIFICATION_UNMATCHING:
    #     ef_attribute = CardFileAttribute.IEF_INTERNAL_AUTHENTICATE_KEY
    #     if status.verification_remaining() == 0:
    #         ef_attribute |= CardFileAttribute.LOCKED
    #     return ef_attribute

    # IEF/EXTERNAL_AUTHENTICATE_KEY
    status, data = connection.external_authenticate(None, cla=cla, raise_error=False)
    status_type = status.status_type()
    if status_type == CardResponseStatusType.VERIFICATION_UNMATCHING:
        ef_attribute = CardFileAttribute.IEF_EXTERNAL_AUTHENTICATE_KEY
        if status.verification_remaining() is None:
            ef_attribute |= CardFileAttribute.VERIFICATION_UNLIMITED
        if status.verification_remaining() == 0:
            ef_attribute |= CardFileAttribute.LOCKED

    # IEF/JPKI_SIGN_PRIVATE_KEY
    status, data = connection.jpki_sign(
        b"\x30\x31\x30\x0B\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20\xe3\xb0\xc4\x42\x98\xfc\x1c\x14\x9a\xfb\xf4\xc8\x99\x6f\xb9\x24\x27\xae\x41\xe4\x64\x9b\x93\x4c\xa4\x95\x99\x1b\x78\x52\xb8\x55",
        raise_error=False,
    )
    status_type = status.status_type()
    if status_type == CardResponseStatusType.NORMAL_END:
        ef_attribute |= CardFileAttribute.JPKI_SIGN_PRIVATE_KEY
    if status_type == CardResponseStatusType.SECURITY_STATUS_NOT_FULFILLED:
        ef_attribute |= (
            CardFileAttribute.JPKI_SIGN_PRIVATE_KEY
            | CardFileAttribute.VERIFICATION_REQUIRED
        )

    # IEF/EXTERNAL_AUTHENTICATE_KEY or IEF/JPKI_SIGN_PRIVATE_KEY
    if ef_attribute != CardFileAttribute.UNKNOWN:
        return ef_attribute

    # WEF/BINARY
    status, data = connection.read_binary(cla=cla, raise_error=False)
    status_type = status.status_type()
    if status_type == CardResponseStatusType.NORMAL_END:
        return CardFileAttribute.WEF_TRANSPARENT
    if status_type == CardResponseStatusType.SECURITY_STATUS_NOT_FULFILLED:
        return CardFileAttribute.VERIFICATION_REQUIRED

    # WEF/RECORD
    status, data = connection.read_record(cla=cla, raise_error=False)
    status_type = status.status_type()
    if status_type == CardResponseStatusType.NORMAL_END:
        return CardFileAttribute.WEF_RECORD
    if status_type == CardResponseStatusType.SECURITY_STATUS_NOT_FULFILLED:
        return CardFileAttribute.VERIFICATION_REQUIRED

    return CardFileAttribute.UNKNOWN


def list_ef(
    connection: CardConnection,
    cla: int = 0x00,
    start: int = 0x0000,
    end: int = 0x10000,
    found_callback: Callable[[bytes, CardFileAttribute], None] | None = None,
) -> list[tuple[bytes, CardFileAttribute]]:
    """List EF

    Args:
        connection (CardConnection): Card Connection
        cla (int, optional): CLA. Defaults to 0x00.
        start (int, optional): Start EF identifier. Defaults to 0x0000.
        end (int, optional): End EF identifier. Defaults to 0x10000.
        found_callback (Callable[[bytes, CardFileAttribute], None], optional): Found callback. Defaults to None.

    Raises:
        ValueError: Invalid argument `cla`
        ValueError: Invalid argument `start`
        ValueError: Invalid argument `end`
        CardResponseError: Card returned error response

    Returns:
        list[tuple[bytes, CardFileAttribute]]: List of EF identifier and Response Status
    """

    if cla < 0x00 or 0xFF < cla:
        raise ValueError("Argument `cla` out of range. (0x00 <= cla <= 0xFF)")
    if start < 0x00:
        raise ValueError("Argument `start` must be greater than or equal 0x0000.")
    if 0x10000 < start:
        raise ValueError("Argument `start` must be less than or equal 0x10000.")
    if end < 0x0000:
        raise ValueError("Argument `end` must be greater than or equal 0x0000.")
    if 0x10000 < end:
        raise ValueError("Argument `end` must be less than or equal 0x10000.")

    ef_list: list[tuple[bytes, CardFileAttribute]] = []
    for ef_id in tqdm(range(start, end), desc="List EF"):
        ef_id_bytes = ef_id.to_bytes(length=2, byteorder="big")
        status, data = connection.select_ef(ef_id_bytes, cla=cla, raise_error=False)
        status_type = status.status_type()
        if (
            status_type == CardResponseStatusType.NORMAL_END
            or status_type == CardResponseStatusType.FILE_CONTROL_INFORMATION_FAILURE
        ):
            ef_attribute = attribute_ef(connection, ef_id_bytes, cla=cla)
            tqdm.write(f"EF {ef_id_bytes.hex().upper()} ({ef_attribute.name}) found.")
            ef_list.append((ef_id_bytes, ef_attribute))
            if found_callback is not None:
                found_callback(ef_id_bytes, ef_attribute)
            continue
        if status_type == CardResponseStatusType.NO_FILE_TO_BE_ACCESSED:
            continue
        raise CardResponseError(status)
    return ef_list


def list_do(
    connection: CardConnection,
    cla: int = 0x00,
    found_callback: Callable[[bytes, bool, bytes], None] | None = None,
) -> list[tuple[bytes, bool]]:
    """List Data Object

    Args:
        connection (CardConnection): Card Connection
        cla (int, optional): CLA. Defaults to 0x00.
        found_callback (Callable[[bytes, bool, bytes], None], optional): Found callback. Defaults to None.

    Raises:
        ValueError: Invalid argument `cla`

    Returns:
        list[tuple[bytes, bool]]: List of tag and simplified encoding
    """

    if cla < 0x00 or 0xFF < cla:
        raise ValueError("Argument `cla` out of range. (0x00 <= cla <= 0xFF)")

    do_list: list[tuple[bytes, bool]] = []

    # 1 byte tag
    for tag in tqdm(range(0x01, 0xFF), desc="List Data Object (1 byte tag)"):
        tag_bytes = tag.to_bytes(length=1)
        status, data = connection.get_data(tag_bytes, cla=cla, raise_error=False)
        status_type = status.status_type()
        if (
            status_type == CardResponseStatusType.NORMAL_END
            or status_type == CardResponseStatusType.INCORRECT_LC_LE_FIELD
        ):
            tqdm.write(f"Data Object {tag_bytes.hex().upper()} (1 byte tag) found.")
            do_list.append((tag_bytes, False))
            if found_callback is not None:
                found_callback(tag_bytes, False, data)

    # Simplified encoding
    for tag in tqdm(range(0x01, 0xFF), desc="List Data Object (Simplified encoding)"):
        tag_bytes = tag.to_bytes(length=1)
        status, data = connection.get_data(
            tag_bytes, simplified_encoding=True, cla=cla, raise_error=False
        )
        status_type = status.status_type()
        if (
            status_type == CardResponseStatusType.NORMAL_END
            or status_type == CardResponseStatusType.INCORRECT_LC_LE_FIELD
        ):
            tqdm.write(
                f"Data Object {tag_bytes.hex().upper()} (Simplified encoding) found."
            )
            do_list.append((tag_bytes, True))
            if found_callback is not None:
                found_callback(tag_bytes, True, data)

    # 2 byte tag
    for tag in tqdm(range(0x1F1F, 0x10000), desc="List Data Object (2 byte tag)"):
        tag_bytes = tag.to_bytes(length=2, byteorder="big")
        status, data = connection.get_data(tag_bytes, cla=cla, raise_error=False)
        status_type = status.status_type()
        if (
            status_type == CardResponseStatusType.NORMAL_END
            or status_type == CardResponseStatusType.INCORRECT_LC_LE_FIELD
        ):
            tqdm.write(f"Data Object {tag_bytes.hex().upper()} (1 byte tag) found.")
            do_list.append((tag_bytes, False))
            if found_callback is not None:
                found_callback(tag_bytes, False, data)

    return do_list
