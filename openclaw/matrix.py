"""
Matrix - 矩阵
基于 Claude Code matrix.ts 设计

矩阵运算工具。
"""
import math
from typing import List


class Matrix:
    """
    矩阵
    
    简单的2D矩阵运算。
    """
    
    def __init__(self, rows: int, cols: int):
        """
        Args:
            rows: 行数
            cols: 列数
        """
        self._rows = rows
        self._cols = cols
        self._data: List[List[float]] = [[0.0] * cols for _ in range(rows)]
    
    @classmethod
    def from_list(cls, data: List[List[float]]) -> "Matrix":
        """从列表创建"""
        if not data:
            raise ValueError("Empty data")
        
        rows = len(data)
        cols = len(data[0])
        
        matrix = cls(rows, cols)
        matrix._data = [[float(x) for x in row] for row in data]
        return matrix
    
    @classmethod
    def identity(cls, size: int) -> "Matrix":
        """单位矩阵"""
        matrix = cls(size, size)
        for i in range(size):
            matrix._data[i][i] = 1.0
        return matrix
    
    @classmethod
    def zeros(cls, rows: int, cols: int) -> "Matrix":
        """零矩阵"""
        return cls(rows, cols)
    
    @classmethod
    def ones(cls, rows: int, cols: int) -> "Matrix":
        """全1矩阵"""
        matrix = cls(rows, cols)
        for i in range(rows):
            for j in range(cols):
                matrix._data[i][j] = 1.0
        return matrix
    
    @property
    def rows(self) -> int:
        return self._rows
    
    @property
    def cols(self) -> int:
        return self._cols
    
    def get(self, row: int, col: int) -> float:
        """获取元素"""
        return self._data[row][col]
    
    def set(self, row: int, col: int, value: float) -> None:
        """设置元素"""
        self._data[row][col] = value
    
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
            raise ValueError("Matrix dimensions incompatible for multiplication")
        
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
            raise ValueError("Determinant only defined for square matrices")
        
        if self._rows == 1:
            return self._data[0][0]
        
        if self._rows == 2:
            return (
                self._data[0][0] * self._data[1][1] -
                self._data[0][1] * self._data[1][0]
            )
        
        # 递归展开（简化实现）
        det = 0
        for j in range(self._cols):
            minor = self._minor(0, j)
            det += ((-1) ** j) * self._data[0][j] * minor.determinant()
        return det
    
    def _minor(self, row: int, col: int) -> "Matrix":
        """余子式"""
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
    
    def inverse(self) -> "Matrix":
        """逆矩阵"""
        det = self.determinant()
        if abs(det) < 1e-10:
            raise ValueError("Matrix is singular")
        
        # 简化实现：2x2矩阵
        if self._rows == 2:
            a, b = self._data[0]
            c, d = self._data[1]
            inv_det = 1.0 / (a * d - b * c)
            result = Matrix(2, 2)
            result._data[0][0] = d * inv_det
            result._data[0][1] = -b * inv_det
            result._data[1][0] = -c * inv_det
            result._data[1][1] = a * inv_det
            return result
        
        raise NotImplementedError("Inverse only implemented for 2x2 matrices")
    
    def __repr__(self) -> str:
        return '\n'.join(' '.join(str(x) for x in row) for row in self._data)


# 导出
__all__ = [
    "Matrix",
]
