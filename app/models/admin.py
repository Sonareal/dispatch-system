from tortoise import fields

from app.schemas.menus import MenuType

from .base import BaseModel, TimestampMixin
from .enums import (
    AuditResult,
    CallStatus,
    FlowAction,
    MessageType,
    MethodType,
    RegionLevel,
    TicketStatus,
)


class User(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=20, unique=True, description="用户名称", index=True)
    alias = fields.CharField(max_length=30, null=True, description="姓名", index=True)
    email = fields.CharField(max_length=255, unique=True, description="邮箱", index=True)
    phone = fields.CharField(max_length=20, null=True, description="电话", index=True)
    password = fields.CharField(max_length=128, null=True, description="密码")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    is_superuser = fields.BooleanField(default=False, description="是否为超级管理员", index=True)
    last_login = fields.DatetimeField(null=True, description="最后登录时间", index=True)
    roles = fields.ManyToManyField("models.Role", related_name="user_roles")
    dept_id = fields.IntField(null=True, description="部门ID", index=True)
    openid = fields.CharField(max_length=128, null=True, unique=True, description="微信OpenID", index=True)
    unionid = fields.CharField(max_length=128, null=True, description="微信UnionID", index=True)
    avatar = fields.CharField(max_length=500, null=True, description="头像URL")
    default_city_id = fields.IntField(null=True, description="默认城市ID", index=True)

    class Meta:
        table = "user"


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="角色名称", index=True)
    code = fields.CharField(max_length=50, null=True, unique=True, description="角色编码", index=True)
    desc = fields.CharField(max_length=500, null=True, description="角色描述")
    menus = fields.ManyToManyField("models.Menu", related_name="role_menus")
    apis = fields.ManyToManyField("models.Api", related_name="role_apis")

    class Meta:
        table = "role"


class Api(BaseModel, TimestampMixin):
    path = fields.CharField(max_length=100, description="API路径", index=True)
    method = fields.CharEnumField(MethodType, description="请求方法", index=True)
    summary = fields.CharField(max_length=500, description="请求简介", index=True)
    tags = fields.CharField(max_length=100, description="API标签", index=True)

    class Meta:
        table = "api"


class Menu(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, description="菜单名称", index=True)
    remark = fields.JSONField(null=True, description="保留字段")
    menu_type = fields.CharEnumField(MenuType, null=True, description="菜单类型")
    icon = fields.CharField(max_length=100, null=True, description="菜单图标")
    path = fields.CharField(max_length=100, description="菜单路径", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, description="父菜单ID", index=True)
    is_hidden = fields.BooleanField(default=False, description="是否隐藏")
    component = fields.CharField(max_length=100, description="组件")
    keepalive = fields.BooleanField(default=True, description="存活")
    redirect = fields.CharField(max_length=100, null=True, description="重定向")

    class Meta:
        table = "menu"


class Dept(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="部门名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="备注")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, max_length=10, description="父部门ID", index=True)

    class Meta:
        table = "dept"


class DeptClosure(BaseModel, TimestampMixin):
    ancestor = fields.IntField(description="父代", index=True)
    descendant = fields.IntField(description="子代", index=True)
    level = fields.IntField(default=0, description="深度", index=True)


class AuditLog(BaseModel, TimestampMixin):
    user_id = fields.IntField(description="用户ID", index=True)
    username = fields.CharField(max_length=64, default="", description="用户名称", index=True)
    module = fields.CharField(max_length=64, default="", description="功能模块", index=True)
    summary = fields.CharField(max_length=128, default="", description="请求描述", index=True)
    method = fields.CharField(max_length=10, default="", description="请求方法", index=True)
    path = fields.CharField(max_length=255, default="", description="请求路径", index=True)
    status = fields.IntField(default=-1, description="状态码", index=True)
    response_time = fields.IntField(default=0, description="响应时间(单位ms)", index=True)
    request_args = fields.JSONField(null=True, description="请求参数")
    response_body = fields.JSONField(null=True, description="返回数据")


# ==================== 派单系统模型 ====================


class City(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, unique=True, description="城市名称", index=True)
    code = fields.CharField(max_length=20, unique=True, description="城市编码", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    order = fields.IntField(default=0, description="排序")

    class Meta:
        table = "city"


class UserCity(BaseModel, TimestampMixin):
    user_id = fields.IntField(description="用户ID", index=True)
    city_id = fields.IntField(description="城市ID", index=True)

    class Meta:
        table = "user_city"
        unique_together = (("user_id", "city_id"),)


class Region(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=100, description="区域名称", index=True)
    code = fields.CharField(max_length=20, null=True, description="区域编码", index=True)
    parent_id = fields.IntField(default=0, description="父级ID", index=True)
    level = fields.CharEnumField(RegionLevel, description="层级", index=True)
    city_id = fields.IntField(null=True, description="所属城市ID", index=True)
    manager_id = fields.IntField(null=True, description="负责人ID(兼容)", index=True)

    class Meta:
        table = "region"


class RegionManager(BaseModel, TimestampMixin):
    """区域负责人关联表 - 支持一个区域多个负责人，一个负责人多个区域"""
    region_id = fields.IntField(description="区域ID", index=True)
    user_id = fields.IntField(description="用户ID", index=True)

    class Meta:
        table = "region_manager"
        unique_together = (("region_id", "user_id"),)


class OrderTicket(BaseModel, TimestampMixin):
    ticket_no = fields.CharField(max_length=32, unique=True, description="工单号", index=True)
    customer_name = fields.CharField(max_length=50, description="客户姓名", index=True)
    customer_phone = fields.CharField(max_length=20, description="联系电话", index=True)
    id_card = fields.CharField(max_length=18, null=True, description="身份证号")
    apply_amount = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="申请金额")
    repayment_method = fields.CharField(max_length=50, null=True, description="还款方式")
    address = fields.CharField(max_length=500, null=True, description="详细地址")
    salesman = fields.CharField(max_length=50, null=True, description="业务员")
    inspection_fee = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="考察费")
    remark = fields.TextField(null=True, description="备注")
    voice_file = fields.CharField(max_length=500, null=True, description="语音文件地址")
    attachment = fields.JSONField(null=True, description="附件列表")
    city_id = fields.IntField(description="城市ID", index=True)
    province_id = fields.IntField(null=True, description="省ID", index=True)
    district_id = fields.IntField(null=True, description="市/区ID", index=True)
    region_id = fields.IntField(null=True, description="区域ID", index=True)
    submitter_id = fields.IntField(description="提交人ID", index=True)
    assignee_id = fields.IntField(null=True, description="当前处理人ID", index=True)
    reviewer_id = fields.IntField(null=True, description="审核人ID", index=True)
    status = fields.CharEnumField(TicketStatus, default=TicketStatus.PENDING_REVIEW, description="工单状态", index=True)
    is_timeout = fields.BooleanField(default=False, description="是否超时")
    last_process_time = fields.DatetimeField(null=True, description="最后处理时间")

    class Meta:
        table = "order_ticket"


class OrderFlow(BaseModel, TimestampMixin):
    ticket_id = fields.IntField(description="工单ID", index=True)
    action = fields.CharEnumField(FlowAction, description="操作类型", index=True)
    from_status = fields.CharField(max_length=30, null=True, description="操作前状态")
    to_status = fields.CharField(max_length=30, null=True, description="操作后状态")
    operator_id = fields.IntField(description="操作人ID", index=True)
    remark = fields.TextField(null=True, description="操作备注")
    transfer_to_id = fields.IntField(null=True, description="转派目标人ID", index=True)

    class Meta:
        table = "order_flow"


class AuditRecord(BaseModel, TimestampMixin):
    ticket_id = fields.IntField(description="工单ID", index=True)
    reviewer_id = fields.IntField(description="审核人ID", index=True)
    result = fields.CharEnumField(AuditResult, description="审核结果", index=True)
    reject_reason = fields.TextField(null=True, description="驳回原因")
    remark = fields.TextField(null=True, description="备注")
    assign_to_id = fields.IntField(null=True, description="指派给", index=True)

    class Meta:
        table = "audit_record"


class MessageRecord(BaseModel, TimestampMixin):
    ticket_id = fields.IntField(description="工单ID", index=True)
    sender_id = fields.IntField(description="发送人ID", index=True)
    receiver_id = fields.IntField(null=True, description="接收人ID", index=True)
    msg_type = fields.CharEnumField(MessageType, default=MessageType.TEXT, description="消息类型", index=True)
    content = fields.TextField(null=True, description="消息内容")
    file_url = fields.CharField(max_length=500, null=True, description="文件地址")
    voice_duration = fields.IntField(null=True, description="语音时长(秒)")
    is_read = fields.BooleanField(default=False, description="是否已读", index=True)

    class Meta:
        table = "message_record"


class MessageReadStatus(BaseModel, TimestampMixin):
    """Per-user read status for messages"""
    message_id = fields.IntField(description="消息ID", index=True)
    user_id = fields.IntField(description="用户ID", index=True)
    read_at = fields.DatetimeField(auto_now_add=True, description="已读时间")

    class Meta:
        table = "message_read_status"
        unique_together = (("message_id", "user_id"),)


class CallRecord(BaseModel, TimestampMixin):
    ticket_id = fields.IntField(description="工单ID", index=True)
    caller_id = fields.IntField(description="发起人ID", index=True)
    callee_id = fields.IntField(description="接听人ID", index=True)
    status = fields.CharEnumField(CallStatus, default=CallStatus.INITIATING, description="通话状态", index=True)
    start_time = fields.DatetimeField(null=True, description="开始时间")
    end_time = fields.DatetimeField(null=True, description="结束时间")
    duration = fields.IntField(default=0, description="通话时长(秒)")
    room_id = fields.CharField(max_length=100, null=True, description="房间ID")

    class Meta:
        table = "call_record"


class OperationLog(BaseModel, TimestampMixin):
    module = fields.CharField(max_length=64, description="功能模块", index=True)
    action = fields.CharField(max_length=64, description="操作类型", index=True)
    operator_id = fields.IntField(description="操作人ID", index=True)
    operator_name = fields.CharField(max_length=64, null=True, description="操作人姓名")
    content = fields.TextField(null=True, description="操作内容")
    ip = fields.CharField(max_length=50, null=True, description="IP地址")

    class Meta:
        table = "operation_log"


class SystemConfig(BaseModel, TimestampMixin):
    key = fields.CharField(max_length=100, unique=True, description="配置键", index=True)
    value = fields.TextField(null=True, description="配置值")
    desc = fields.CharField(max_length=200, null=True, description="配置说明")
    group = fields.CharField(max_length=50, null=True, description="配置分组", index=True)

    class Meta:
        table = "system_config"
