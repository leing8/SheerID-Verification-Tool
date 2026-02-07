"""
大学文档模板抽象基类
定义所有大学模板必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List


class UniversityTemplate(ABC):
    """
    大学文档模板抽象基类
    
    每个具体的大学模板（或通用模板）都需要继承此类并实现相应方法。
    模板可以支持一个或多个大学ID。
    """
    
    @property
    @abstractmethod
    def university_ids(self) -> List[int]:
        """
        支持的大学ID列表
        
        返回此模板支持的所有大学ID。
        对于通用模板，可以返回空列表表示支持所有大学。
        """
        pass
    
    @property
    def template_name(self) -> str:
        """模板名称（用于日志）"""
        return self.__class__.__name__
    
    @abstractmethod
    def generate_transcript(
        self, 
        first: str, 
        last: str, 
        school: str,
        dob: str, 
        seed: str
    ) -> bytes:
        """
        生成学术成绩单
        
        参数:
            first: 名
            last: 姓
            school: 学校名称
            dob: 出生日期
            seed: 随机种子（verificationId）
        
        返回:
            PNG 格式的图像字节数据
        """
        pass
    
    @abstractmethod
    def generate_student_id(
        self, 
        first: str, 
        last: str, 
        school: str,
        seed: str
    ) -> bytes:
        """
        生成学生证
        
        参数:
            first: 名
            last: 姓
            school: 学校名称
            seed: 随机种子（verificationId）
        
        返回:
            PNG 格式的图像字节数据
        """
        pass
    
    def generate_receipt(
        self, 
        first: str, 
        last: str, 
        school: str,
        seed: str,
        receipt_type: str = "tuition"
    ) -> bytes:
        """
        生成收据（可选实现）
        
        参数:
            first: 名
            last: 姓
            school: 学校名称
            seed: 随机种子
            receipt_type: 收据类型 ("tuition" 学费, "bookstore" 书店)
        
        返回:
            PNG 格式的图像字节数据
        
        默认抛出 NotImplementedError，子类可选择性覆盖
        """
        raise NotImplementedError(f"{self.template_name} 不支持收据生成")
    
    def supports_receipt(self) -> bool:
        """是否支持收据生成"""
        return False
