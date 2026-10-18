"""恢复电量的数量边界与节点结果测试，不创建窗口或发送输入。"""

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

if TYPE_CHECKING:
    from zzz_od.operation.restore_charge import RestoreCharge


@pytest.fixture(scope='module')
def restore_module() -> ModuleType:
    """加载真实操作模块，仅隔离依赖 Windows 的上下文和操作基类。

    不调用构造函数或自动化执行入口；数量判断和节点方法保持真实实现。
    临时替身只在模块加载期间生效，离开后恢复，不影响其他测试。
    """
    context_module = ModuleType('zzz_od.context.zzz_context')
    context_module.ZContext = object
    operation_module = ModuleType('zzz_od.operation.zzz_operation')
    operation_module.ZOperation = object
    source = (
        Path(__file__).resolve().parents[4]
        / 'src/zzz_od/operation/restore_charge.py'
    )
    spec = importlib.util.spec_from_file_location('_restore_charge_unit_test', source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        'sys.modules',
        {
            'zzz_od.context.zzz_context': context_module,
            'zzz_od.operation.zzz_operation': operation_module,
        },
    ):
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ('current_amount', 'exchange_amount', 'expected'),
    [
        (1, 1, True),
        (17, 17, True),
        (60, 60, True),
        (2, 1, True),
        (2400, 17, True),
        (1, 2, False),
        (0, 1, False),
        (0, 0, False),
    ],
)
def test_restore_amount_boundary(
    restore_module: ModuleType,
    current_amount: int,
    exchange_amount: int,
    expected: bool,
) -> None:
    """库存刚好够用或有余量时允许确认，不足及空库存时不确认。"""
    op = restore_module.RestoreCharge.__new__(restore_module.RestoreCharge)
    assert op._should_confirm_restore(current_amount, exchange_amount) is expected


def _make_operation(
    restore_module: ModuleType,
    source: str | None,
    current_amount: int | None,
    exchange_amount: int | None,
    restore_mode: str,
) -> 'RestoreCharge':
    """注入识别结果，记录节点返回，避免截图、读配置和真实点击。"""
    op = restore_module.RestoreCharge.__new__(restore_module.RestoreCharge)
    op.config = SimpleNamespace(restore_charge=restore_mode)
    op.previous_node = SimpleNamespace(status=source)
    op.skip_backup_charge = False
    op._get_amount_by_area = Mock(side_effect=[current_amount, exchange_amount])
    op.round_success = Mock()
    op.round_retry = Mock()
    return op


@pytest.mark.parametrize(
    ('source', 'current_amount', 'mode_name'),
    [
        ('以太电池', 1, 'ETHER_ONLY'),
        ('储蓄电量', 17, 'BACKUP_ONLY'),
        ('储蓄电量', 17, 'BOTH'),
    ],
)
def test_exact_stock_keeps_selected_source(
    restore_module: ModuleType,
    source: str,
    current_amount: int,
    mode_name: str,
) -> None:
    """刚好用完库存仍进入确认节点，不报不足，也不改用另一来源。"""
    mode = getattr(restore_module.RestoreChargeEnum, mode_name).value.value
    op = _make_operation(restore_module, source, current_amount, current_amount, mode)

    result = op.set_charge_amount()

    assert result is op.round_success.return_value
    op.round_success.assert_called_once_with(
        status=source, data=current_amount, wait=0.5
    )
    op.round_retry.assert_not_called()
    assert op.skip_backup_charge is False


@pytest.mark.parametrize(
    ('source', 'current_amount', 'exchange_amount', 'expected_status'),
    [
        (None, 1, 1, '未识别到电量来源'),
        ('以太电池', None, 1, '未识别到当前数量'),
        ('以太电池', 1, None, '未识别到兑换数量'),
        ('以太电池', 1, 2, '兑换数量大于当前数量'),
    ],
)
def test_unreadable_or_insufficient_amount_still_retries(
    restore_module: ModuleType,
    source: str | None,
    current_amount: int | None,
    exchange_amount: int | None,
    expected_status: str,
) -> None:
    """读取失败和超出库存仍走原有重试，不因为修复边界而放行。"""
    mode = restore_module.RestoreChargeEnum.ETHER_ONLY.value.value
    op = _make_operation(restore_module, source, current_amount, exchange_amount, mode)

    result = op.set_charge_amount()

    assert result is op.round_retry.return_value
    op.round_retry.assert_called_once_with(expected_status, wait=0.5)
    op.round_success.assert_not_called()
