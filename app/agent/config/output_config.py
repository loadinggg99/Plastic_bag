"""结构化输出模型：一个域一个 Pydantic 模型。

约定：
- 字段均可为 None，查不到的字段返回 null，to_display() 统一渲染「未查到」；
- 展示文本由 to_display() 生成，不交给 LLM 二次排版；
- source_url 不进入 LLM schema，由工具层从 Tavily 结果回填。
"""

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


def _value(text: str | None) -> str:
    """查不到的字段统一显示「未查到」。"""
    return text or "未查到"


def _block(title: str, lines: list[tuple[str, str | None]]) -> str:
    """渲染一段带小标题的字段块，如：

        【基础工商信息】
        企业名称：xxx
        经营状态：未查到
    """
    body = "\n".join(f"{label}：{_value(text)}" for label, text in lines)
    return f"【{title}】\n{body}"


class _DomainModel(BaseModel):
    """六个域输出模型的公共基类。

    `source_url` 用 `SkipJsonSchema` 包住，因此**不会**出现在
    `with_structured_output()` 生成的函数参数 schema 里：模型看不到这个字段，
    也不需要（更不能）生成它。真实链接由 `extract_structured()` 从 Tavily
    原始搜索结果里回填，从根上避免模型编造 URL。
    """

    source_url: SkipJsonSchema[str | None] = Field(
        default=None,
        description=(
            "数据来源URL，由工具从 Tavily 搜索结果中自动回填；"
            "多个链接用顿号分隔，查不到则为 null"
        ),
    )


class BasicBusinessInfo(_DomainModel):
    """基础工商信息：查询任何公司最先看到的部分"""

    company_name: str | None = Field(
        default=None,
        description="企业名称，公司当前工商登记的全称"
    )
    former_names: str | None = Field(
        default=None,
        description="曾用名，公司历史上用过的名称；没有则返回 null"
    )
    credit_code: str | None = Field(
        default=None,
        description="统一社会信用代码"
    )
    registration_number: str | None = Field(
        default=None,
        description="工商注册号"
    )
    organization_code: str | None = Field(
        default=None,
        description="组织机构代码"
    )
    taxpayer_id: str | None = Field(
        default=None,
        description="纳税人识别号"
    )
    legal_representative: str | None = Field(
        default=None,
        description="法定代表人姓名"
    )
    registered_capital: str | None = Field(
        default=None,
        description="注册资本（认缴），如 '1000万元人民币'"
    )
    paid_in_capital: str | None = Field(
        default=None,
        description="实缴资本，如 '500万元人民币'"
    )
    founded_date: str | None = Field(
        default=None,
        description="成立日期，格式如 '2015-03-12' 或 '2015年3月'"
    )
    business_term: str | None = Field(
        default=None,
        description="营业期限，如 '2015-03-12 至 长期'"
    )
    operation_status: str | None = Field(
        default=None,
        description="经营状态，如存续、开业、注销、吊销、迁出"
    )
    company_type: str | None = Field(
        default=None,
        description="企业类型，如有限责任公司、股份有限公司"
    )
    registered_address: str | None = Field(
        default=None,
        description="注册地址"
    )
    business_scope: str | None = Field(
        default=None,
        description="经营范围"
    )
    registration_authority: str | None = Field(
        default=None,
        description="登记机关"
    )
    approval_date: str | None = Field(
        default=None,
        description="核准日期，格式如 '2024-06-01'"
    )
    industry: str | None = Field(
        default=None,
        description="所属行业，如软件和信息技术服务业"
    )

    def to_display(self) -> str:
        return _block("基础工商信息", [
            ("企业名称", self.company_name),
            ("曾用名", self.former_names),
            ("统一社会信用代码", self.credit_code),
            ("工商注册号", self.registration_number),
            ("组织机构代码", self.organization_code),
            ("纳税人识别号", self.taxpayer_id),
            ("法定代表人", self.legal_representative),
            ("注册资本", self.registered_capital),
            ("实缴资本", self.paid_in_capital),
            ("成立日期", self.founded_date),
            ("营业期限", self.business_term),
            ("经营状态", self.operation_status),
            ("企业类型", self.company_type),
            ("注册地址", self.registered_address),
            ("经营范围", self.business_scope),
            ("登记机关", self.registration_authority),
            ("核准日期", self.approval_date),
            ("所属行业", self.industry),
            ("数据来源URL", self.source_url),
        ])


class PersonnelEquityStructure(_DomainModel):
    """人员与股权结构：人和钱的归属"""

    key_personnel: str | None = Field(
        default=None,
        description="主要人员，包括法定代表人、董事、监事、经理等高管及其职务"
    )
    shareholders: str | None = Field(
        default=None,
        description=(
            "股东信息，逐个列出股东名称/姓名、持股比例、认缴出资额、实缴出资额、"
            "出资方式、出资日期"
        )
    )
    ultimate_beneficiaries: str | None = Field(
        default=None,
        description="最终受益人，通过股权穿透计算出的实际享有收益的自然人及其受益比例"
    )
    actual_controller: str | None = Field(
        default=None,
        description="实际控制人，对公司拥有实际控制权的自然人或组织，以及控制路径"
    )
    equity_penetration: str | None = Field(
        default=None,
        description=(
            "股权穿透图/企业关系图谱，用文字描述公司—股东—对外投资之间的"
            "控制与关联关系（建议用 A 持股 B 60% -> C 的层级写法），"
            "并给出可查看图谱的来源链接"
        )
    )

    def to_display(self) -> str:
        return _block("人员与股权结构", [
            ("主要人员", self.key_personnel),
            ("股东信息", self.shareholders),
            ("最终受益人", self.ultimate_beneficiaries),
            ("实际控制人", self.actual_controller),
            ("股权穿透图/企业关系图谱", self.equity_penetration),
            ("数据来源URL", self.source_url),
        ])


class BusinessFinancialStatus(_DomainModel):
    """经营与财务状况：财务、上市、投资、融资与年报"""

    financials: str | None = Field(
        default=None,
        description="财务数据，如营收、净利润、资产负债等指标（上市公司为主）"
    )
    listing_info: str | None = Field(
        default=None,
        description="上市信息，如股票代码、上市日期、所属板块、股价行情"
    )
    outbound_investments: str | None = Field(
        default=None,
        description="对外投资，公司直接投资的企业列表及持股比例"
    )
    branches: str | None = Field(
        default=None,
        description="分支机构，公司的分公司或子公司"
    )
    financing_history: str | None = Field(
        default=None,
        description="融资历史，历次融资的轮次、时间、金额、投资方"
    )
    annual_reports: str | None = Field(
        default=None,
        description="企业年报，每年自主公示的年度报告，含资产状况、社保人数等"
    )
    bidding: str | None = Field(
        default=None,
        description="招投标，公司参与的招标与中标公告"
    )

    def to_display(self) -> str:
        return _block("经营与财务状况", [
            ("财务数据", self.financials),
            ("上市信息", self.listing_info),
            ("对外投资", self.outbound_investments),
            ("分支机构", self.branches),
            ("融资历史", self.financing_history),
            ("企业年报", self.annual_reports),
            ("招投标", self.bidding),
            ("数据来源URL", self.source_url),
        ])


class RiskJudicialInfo(_DomainModel):
    """风险与司法信息：合规与信用状况"""

    judicial_risk: str | None = Field(
        default=None,
        description="司法风险，如法律诉讼、法院公告、开庭公告、裁判文书（案由、身份、时间、结果）"
    )
    execution_info: str | None = Field(
        default=None,
        description="执行信息，如被执行人、失信被执行人、限制消费令、终本案件"
    )
    operation_risk: str | None = Field(
        default=None,
        description="经营风险，如经营异常、行政处罚、股权出质、股权冻结、动产抵押"
    )
    tax_risk: str | None = Field(
        default=None,
        description="税务风险，如欠税公告、税务异常"
    )
    bankruptcy: str | None = Field(
        default=None,
        description="破产重整，如破产案件信息、重整申请、破产审查"
    )

    def to_display(self) -> str:
        return _block("风险与司法信息", [
            ("司法风险", self.judicial_risk),
            ("执行信息", self.execution_info),
            ("经营风险", self.operation_risk),
            ("税务风险", self.tax_risk),
            ("破产重整", self.bankruptcy),
            ("数据来源URL", self.source_url),
        ])


class IpQualification(_DomainModel):
    """知识产权与资质：商标、专利、著作权与各类许可"""

    trademarks: str | None = Field(
        default=None,
        description="商标，商标名称、类别、申请/注册号、状态"
    )
    patents: str | None = Field(
        default=None,
        description="专利，专利名称、类型（发明/实用新型/外观设计）、申请号、状态"
    )
    copyrights: str | None = Field(
        default=None,
        description="著作权，作品名称、登记号"
    )
    software_copyrights: str | None = Field(
        default=None,
        description="软件著作权，软件名称、登记号"
    )
    qualification_certificates: str | None = Field(
        default=None,
        description="资质证书，各类行业资质、行政许可及其编号、有效期"
    )
    website_filing: str | None = Field(
        default=None,
        description="网站备案，公司官网的 ICP 备案号、网站域名、主办单位性质"
    )

    def to_display(self) -> str:
        return _block("知识产权与资质", [
            ("商标", self.trademarks),
            ("专利", self.patents),
            ("著作权", self.copyrights),
            ("软件著作权", self.software_copyrights),
            ("资质证书", self.qualification_certificates),
            ("网站备案", self.website_filing),
            ("数据来源URL", self.source_url),
        ])


class OperationPublicOpinion(_DomainModel):
    """经营状况与舆情：员工、招聘、新闻与评分"""

    employee_scale: str | None = Field(
        default=None,
        description="员工规模，如参保人数、人员规模"
    )
    recruitment: str | None = Field(
        default=None,
        description="招聘信息，在招职位、薪资范围、工作地点"
    )
    news_public_opinion: str | None = Field(
        default=None,
        description="新闻舆情，与公司相关的新闻、公告、自媒体信息（含正负面倾向）"
    )
    enterprise_score: str | None = Field(
        default=None,
        description="企业评分，如天眼评分或行业评分，以及评分依据"
    )

    def to_display(self) -> str:
        return _block("经营状况与舆情", [
            ("员工规模", self.employee_scale),
            ("招聘信息", self.recruitment),
            ("新闻舆情", self.news_public_opinion),
            ("企业评分", self.enterprise_score),
            ("数据来源URL", self.source_url),
        ])
