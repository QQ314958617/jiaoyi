"""
Matrix - 矩阵
基于 Claude Code matrix.ts 设计

矩阵工具。
"""
from typing import List


class Matrix:
    """
    矩阵
    """
    
    def __init__(self, rows: int, cols: int, default: float = 0):
        """
        Args:
            rows: 行数
            cols: 列数
            default: 默认值
        """
        self._rows = rows
        self._cols = cols
        self._default = default
        self._data = [[default for _ in range(cols)] for _ in range(rows)]
    
    @staticmethod
    def identity(n: int) -> "Matrix":
        """
        单位矩阵
        
        Args:
            n: 维度
            
        Returns:
            n×n单位矩阵
        """
        m = Matrix(n, n)
        for i in range(n):
            m._data[i][i] = 1
        return m
    
    @staticmethod
    def from_list(data: List[List]) -> "Matrix":
        """
        从列表创建
        
        Args:
            data: 二维列表
            
        Returns:
            Matrix实例
        """
        if not data:
            return Matrix(0, 0)
        rows = len(data)
        cols = len(data[0]) if data[0] else 0
        m = Matrix(rows, cols)
        m._data = [row[:] for row in data]
        return m
    
    def get(self, row: int, col: int) -> float:
        """获取元素"""
        if 0 <= row < self._rows and 0 <= col < self._cols:
            return self._data[row][col]
        raise IndexError(f"Index ({row}, {col}) out of bounds")
    
    def set(self, row: int, col: int, value: float) -> None:
        """设置元素"""
        if 0 <= row < self._rows and 0 <= col < self._cols:
            self._data[row][col] = value
        else:
            raise IndexError(f"Index ({row}, {col}) out of bounds")
    
    def add(self, other: "Matrix") -> "Matrix":
        """矩阵加法"""
        if self._rows != other._rows or self._cols != other._cols:
            raise ValueError("Matrix dimensions must match")
        
        result = Matrix(self._rows, self._cols)
        for i in range(self._rows):
            for j in range(self._cols):
                result._data[i][j] = self._data[i][j] + other._data[i][j]
        return result
    
    def subtract(self, other: "Matrix") -> "Matrix":
        """矩阵减法"""
        if self._rows != other._rows or self._cols != other._cols:
            raise ValueError("Matrix dimensions must match")
        
        result = Matrix(self._rows, self._cols)
        for i in range(self._rows):
            for j in range(self._cols):
                result._data[i][j] = self._data[i][j] - other._data[i][j]
        return result
    
    def multiply(self, other: "Matrix") -> "Matrix":
        """矩阵乘法"""
        if self._cols != other._rows:
            raise ValueError(f"Cannot multiply: {self._cols} != {other._rows}")
        
        result = Matrix(self._rows, other._cols)
        for i in range(self._rows):
            for j in range(other._cols):
                total = 0
                for k in range(self._cols):
                    total += self._data[i][k] * other._data[k][j]
                result._data[i][j] = total
        return result
    
    def scale(self, scalar: float) -> "Matrix":
        """标量乘法"""
        result = Matrix(self._rows, self._cols)
        for i in range(self._rows):
            for j in range(self._cols):
                result._data[i][j] = self._data[i][j] * scalar
        return result
    
    def transpose(self) -> "Matrix":
        """转置"""
        result = Matrix(self._cols, self._rows)
        for i in range(self._rows):
            for j in range(self._cols):
                result._data[j][i] = self._data[i][j]
        return result
    
    def determinant(self) -> float:
        """行列式（仅方阵）"""
        if self._rows != self._cols:
            raise ValueError("Determinant requires square matrix")
        
        if self._rows == 1:
            return self._data[0][0]
        if self._rows == 2:
            return self._data[0][0] * self._data[1][1] - self._data[0][1] * self._data[1][0]
        
        # 递归展开（简化版，仅适用于小矩阵）
        det = 0
        for j in range(self._cols):
            minor = self._get_minor(0, j)
            det += ((-1) ** j) * self._data[0][j] * minor.determinant()
        return det
    
    def _get_minor(self, row: int, col: int) -> "Matrix":
        """获取余子式"""
        result = Matrix(self._rows - 1, self._cols - 1)
        r = 0
        for i in range(self._rows):
            if i == row:
                continue
            c = 0
            for j in range(self._cols):
                if j == col:
                    continue
                result._data[r][c] = self._data[i][j]
                c += 1
            r += 1
        return result
    
    @property
    def rows(self) -> int:
        return self._rows
    
    @property
    def cols(self) -> int:
        return self._cols
    
    def to_list(self) -> List[List]:
        """转为列表"""
        return [row[:] for row in self._data]
    
    def __str__(self) -> str:
        return '\n'.join(' '.join(str(x) for x in row) for row in self._data)


# 导出
__all__ = [
    "Matrix",
]
