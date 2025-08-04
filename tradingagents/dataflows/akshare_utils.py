#!/usr/bin/env python3
"""
AKShare数据源工具
提供AKShare数据获取的统一接口
"""

import pandas as pd
from typing import Optional, Dict, Any
import warnings
from datetime import datetime

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')
warnings.filterwarnings('ignore')

class AKShareProvider:
    """AKShare数据提供器"""

    def __init__(self):
        """初始化AKShare提供器"""
        try:
            import akshare as ak
            self.ak = ak
            self.connected = True

            # 设置更长的超时时间
            self._configure_timeout()

            logger.info(f"✅ AKShare初始化成功")
        except ImportError:
            self.ak = None
            self.connected = False
            logger.error(f"❌ AKShare未安装")

    def _configure_timeout(self):
        """配置AKShare的超时设置"""
        try:
            import requests
            import socket

            # 设置更长的超时时间
            socket.setdefaulttimeout(60)  # 60秒超时

            # 如果AKShare使用requests，设置默认超时
            if hasattr(requests, 'adapters'):
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                # 创建重试策略
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )

                # 设置适配器
                adapter = HTTPAdapter(max_retries=retry_strategy)
                session = requests.Session()
                session.mount("http://", adapter)
                session.mount("https://", adapter)

                logger.info(f"🔧 AKShare超时配置完成: 60秒超时，3次重试")

        except Exception as e:
            logger.error(f"⚠️ AKShare超时配置失败: {e}")
            logger.info(f"🔧 使用默认超时设置")
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        if not self.connected:
            return None
        
        try:
            # 转换股票代码格式
            if len(symbol) == 6:
                symbol = symbol
            else:
                symbol = symbol.replace('.SZ', '').replace('.SS', '')
            
            # 获取数据
            data = self.ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace('-', '') if start_date else "20240101",
                end_date=end_date.replace('-', '') if end_date else "20241231",
                adjust=""
            )
            
            return data
            
        except Exception as e:
            logger.error(f"❌ AKShare获取股票数据失败: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        if not self.connected:
            return {}
        
        try:
            # 获取股票基本信息
            stock_list = self.ak.stock_info_a_code_name()
            stock_info = stock_list[stock_list['code'] == symbol]
            
            if not stock_info.empty:
                return {
                    'symbol': symbol,
                    'name': stock_info.iloc[0]['name'],
                    'source': 'akshare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}
                
        except Exception as e:
            logger.error(f"❌ AKShare获取股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'akshare'}

    def get_hk_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取港股历史数据

        Args:
            symbol: 港股代码 (如: 00700 或 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame: 港股历史数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接")
            return None

        try:
            # 标准化港股代码 - AKShare使用5位数字格式
            hk_symbol = self._normalize_hk_symbol_for_akshare(symbol)

            logger.info(f"🇭🇰 AKShare获取港股数据: {hk_symbol} ({start_date} 到 {end_date})")

            # 格式化日期为AKShare需要的格式
            start_date_formatted = start_date.replace('-', '') if start_date else "20240101"
            end_date_formatted = end_date.replace('-', '') if end_date else "20241231"

            # 使用AKShare获取港股历史数据（带超时保护）
            import threading

            result = [None]
            exception = [None]

            def fetch_hist_data():
                try:
                    result[0] = self.ak.stock_hk_hist(
                        symbol=hk_symbol,
                        period="daily",
                        start_date=start_date_formatted,
                        end_date=end_date_formatted,
                        adjust=""
                    )
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_hist_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare港股历史数据获取超时（60秒）: {symbol}")
                raise Exception(f"AKShare港股历史数据获取超时（60秒）: {symbol}")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                data = result[0]

            if not data.empty:
                # 数据预处理
                data = data.reset_index()
                data['Symbol'] = symbol  # 保持原始格式

                # 重命名列以保持一致性
                column_mapping = {
                    '日期': 'Date',
                    '开盘': 'Open',
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume',
                    '成交额': 'Amount'
                }

                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns:
                        data = data.rename(columns={old_col: new_col})

                logger.info(f"✅ AKShare港股数据获取成功: {symbol}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare港股数据为空: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取港股数据失败: {e}")
            return None

    def get_hk_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取港股基本信息

        Args:
            symbol: 港股代码

        Returns:
            Dict: 港股基本信息
        """
        if not self.connected:
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare_unavailable'
            }

        try:
            hk_symbol = self._normalize_hk_symbol_for_akshare(symbol)

            logger.info(f"🇭🇰 AKShare获取港股信息: {hk_symbol}")

            # 尝试获取港股实时行情数据来获取基本信息
            # 使用线程超时包装（兼容Windows）
            import threading


            result = [None]
            exception = [None]

            def fetch_data():
                try:
                    result[0] = self.ak.stock_hk_spot_em()
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare港股信息获取超时（60秒），使用备用方案")
                raise Exception("AKShare港股信息获取超时（60秒）")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                spot_data = result[0]

            # 查找对应的股票信息
            if not spot_data.empty:
                # 查找匹配的股票
                matching_stocks = spot_data[spot_data['代码'].str.contains(hk_symbol[:5], na=False)]

                if not matching_stocks.empty:
                    stock_info = matching_stocks.iloc[0]
                    return {
                        'symbol': symbol,
                        'name': stock_info.get('名称', f'港股{symbol}'),
                        'currency': 'HKD',
                        'exchange': 'HKG',
                        'latest_price': stock_info.get('最新价', None),
                        'source': 'akshare'
                    }

            # 如果没有找到，返回基本信息
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare'
            }

        except Exception as e:
            logger.error(f"❌ AKShare获取港股信息失败: {e}")
            return {
                'symbol': symbol,
                'name': f'港股{symbol}',
                'currency': 'HKD',
                'exchange': 'HKG',
                'source': 'akshare_error',
                'error': str(e)
            }

    def _normalize_hk_symbol_for_akshare(self, symbol: str) -> str:
        """
        标准化港股代码为AKShare格式

        Args:
            symbol: 原始港股代码 (如: 0700.HK 或 700)

        Returns:
            str: AKShare格式的港股代码 (如: 00700)
        """
        if not symbol:
            return symbol

        # 移除.HK后缀
        clean_symbol = symbol.replace('.HK', '').replace('.hk', '')

        # 确保是5位数字格式
        if clean_symbol.isdigit():
            return clean_symbol.zfill(5)

        return clean_symbol

    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票财务数据
        
        Args:
            symbol: 股票代码 (6位数字)
            
        Returns:
            Dict: 包含主要财务指标的财务数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取{symbol}财务数据")
            return {}
        
        try:
            logger.info(f"🔍 开始获取{symbol}的AKShare财务数据")
            
            financial_data = {}
            
            # 1. 优先获取主要财务指标
            try:
                logger.debug(f"📊 尝试获取{symbol}主要财务指标...")
                main_indicators = self.ak.stock_financial_abstract(symbol=symbol)
                if main_indicators is not None and not main_indicators.empty:
                    financial_data['main_indicators'] = main_indicators
                    logger.info(f"✅ 成功获取{symbol}主要财务指标: {len(main_indicators)}条记录")
                    logger.debug(f"主要财务指标列名: {list(main_indicators.columns)}")
                else:
                    logger.warning(f"⚠️ {symbol}主要财务指标为空")
            except Exception as e:
                logger.warning(f"❌ 获取{symbol}主要财务指标失败: {e}")
            
            # 2. 尝试获取资产负债表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}资产负债表...")
                balance_sheet = self.ak.stock_balance_sheet_by_report_em(symbol=symbol)
                if balance_sheet is not None and not balance_sheet.empty:
                    financial_data['balance_sheet'] = balance_sheet
                    logger.debug(f"✅ 成功获取{symbol}资产负债表: {len(balance_sheet)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}资产负债表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}资产负债表失败: {e}")
            
            # 3. 尝试获取利润表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}利润表...")
                income_statement = self.ak.stock_profit_sheet_by_report_em(symbol=symbol)
                if income_statement is not None and not income_statement.empty:
                    financial_data['income_statement'] = income_statement
                    logger.debug(f"✅ 成功获取{symbol}利润表: {len(income_statement)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}利润表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}利润表失败: {e}")
            
            # 4. 尝试获取现金流量表（可能失败，降级为debug日志）
            try:
                logger.debug(f"📊 尝试获取{symbol}现金流量表...")
                cash_flow = self.ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
                if cash_flow is not None and not cash_flow.empty:
                    financial_data['cash_flow'] = cash_flow
                    logger.debug(f"✅ 成功获取{symbol}现金流量表: {len(cash_flow)}条记录")
                else:
                    logger.debug(f"⚠️ {symbol}现金流量表为空")
            except Exception as e:
                logger.debug(f"❌ 获取{symbol}现金流量表失败: {e}")
            
            # 记录最终结果
            if financial_data:
                logger.info(f"✅ AKShare财务数据获取完成: {symbol}, 包含{len(financial_data)}个数据集")
                for key, value in financial_data.items():
                    if hasattr(value, '__len__'):
                        logger.info(f"  - {key}: {len(value)}条记录")
            else:
                logger.warning(f"⚠️ 未能获取{symbol}的任何AKShare财务数据")
            
            return financial_data
            
        except Exception as e:
            logger.error(f"❌ AKShare获取{symbol}财务数据失败: {e}")
            return {}

    def get_sw_index_hist(self, symbol: str, period: str = "day") -> Optional[pd.DataFrame]:
        """
        获取申万指数历史行情数据
        
        Args:
            symbol: 申万指数代码（如：801010, 801193）
            period: 数据周期（"day", "week", "month"）
        
        Returns:
            pd.DataFrame: 申万指数历史行情数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取申万指数数据")
            return None

        try:
            logger.info(f"📊 AKShare获取申万指数历史数据: {symbol}, 周期: {period}")

            # 使用线程超时包装
            import threading
            result = [None]
            exception = [None]

            def fetch_sw_index_data():
                try:
                    result[0] = self.ak.index_hist_sw(symbol=symbol, period=period)
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_sw_index_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                logger.warning(f"⚠️ AKShare申万指数历史数据获取超时（60秒）: {symbol}")
                raise Exception(f"申万指数历史数据获取超时（60秒）: {symbol}")
            elif exception[0]:
                raise exception[0]
            else:
                data = result[0]

            if data is not None and not data.empty:
                # 数据预处理
                data = data.reset_index()
                data['Symbol'] = symbol  # 添加股票代码

                # 标准化列名
                column_mapping = {
                    '日期': 'Date',
                    '开盘': 'Open',
                    '收盘': 'Close',
                    '最高': 'High',
                    '最低': 'Low',
                    '成交量': 'Volume',
                    '成交额': 'Amount'
                }

                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns:
                        data = data.rename(columns={old_col: new_col})

                logger.info(f"✅ AKShare申万指数数据获取成功: {symbol}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare申万指数数据为空: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取申万指数数据失败: {symbol}, 错误: {e}")
            return None

    def get_sw_index_min(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取申万指数分时行情数据
        
        Args:
            symbol: 申万指数代码（如：801010, 801193）
        
        Returns:
            pd.DataFrame: 申万指数分时行情数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取申万指数分时数据")
            return None

        try:
            logger.info(f"📊 AKShare获取申万指数分时数据: {symbol}")

            # 使用线程超时包装
            import threading
            result = [None]
            exception = [None]

            def fetch_sw_min_data():
                try:
                    result[0] = self.ak.index_min_sw(symbol=symbol)
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_sw_min_data)
            thread.daemon = True
            thread.start()

            # 等待30秒
            thread.join(timeout=30)

            if thread.is_alive():
                logger.warning(f"⚠️ AKShare申万指数分时数据获取超时（30秒）: {symbol}")
                raise Exception(f"申万指数分时数据获取超时（30秒）: {symbol}")
            elif exception[0]:
                raise exception[0]
            else:
                data = result[0]

            if data is not None and not data.empty:
                # 数据预处理
                data = data.reset_index()
                data['Symbol'] = symbol

                logger.info(f"✅ AKShare申万指数分时数据获取成功: {symbol}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare申万指数分时数据为空: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取申万指数分时数据失败: {symbol}, 错误: {e}")
            return None

    def get_sw_components(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取申万指数成分股数据
        
        Args:
            symbol: 申万指数代码（如：801010, 801193）
        
        Returns:
            pd.DataFrame: 申万指数成分股数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取申万指数成分股数据")
            return None

        try:
            logger.info(f"📊 AKShare获取申万指数成分股数据: {symbol}")

            # 使用线程超时包装
            import threading
            result = [None]
            exception = [None]

            def fetch_sw_components_data():
                try:
                    result[0] = self.ak.index_component_sw(symbol=symbol)
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_sw_components_data)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                logger.warning(f"⚠️ AKShare申万指数成分股数据获取超时（60秒）: {symbol}")
                raise Exception(f"申万指数成分股数据获取超时（60秒）: {symbol}")
            elif exception[0]:
                raise exception[0]
            else:
                data = result[0]

            if data is not None and not data.empty:
                # 数据预处理
                data = data.reset_index()
                data['Index_Symbol'] = symbol  # 添加指数代码

                # 标准化列名
                column_mapping = {
                    '序号': 'Rank',
                    '证券代码': 'Code',
                    '证券名称': 'Name',
                    '最新权重': 'Weight',
                    '计入日期': 'Date'
                }

                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns:
                        data = data.rename(columns={old_col: new_col})

                logger.info(f"✅ AKShare申万指数成分股数据获取成功: {symbol}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare申万指数成分股数据为空: {symbol}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取申万指数成分股数据失败: {symbol}, 错误: {e}")
            return None

    def get_sw_industry_list(self) -> Optional[pd.DataFrame]:
        """
        获取申万行业分类列表
        
        Returns:
            pd.DataFrame: 申万行业分类列表
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取申万行业分类")
            return None

        try:
            logger.info(f"📊 AKShare获取申万行业分类列表")

            # 使用线程超时包装
            import threading
            result = [None]
            exception = [None]

            def fetch_sw_industry_list():
                try:
                    # 使用AkShare官方API获取申万三级行业信息
                    result[0] = self.ak.sw_index_third_info()
                except Exception as e:
                    # 如果API调用失败，使用备用数据
                    logger.warning(f"⚠️ AkShare API调用失败，使用备用数据: {e}")
                    sw_industries = [
                        {'code': '801010', 'name': '农林牧渔', 'level': 1},
                        {'code': '801020', 'name': '采掘', 'level': 1},
                        {'code': '801030', 'name': '化工', 'level': 1},
                        {'code': '801040', 'name': '钢铁', 'level': 1},
                        {'code': '801050', 'name': '有色金属', 'level': 1},
                        {'code': '801080', 'name': '电子', 'level': 1},
                        {'code': '801110', 'name': '家用电器', 'level': 1},
                        {'code': '801120', 'name': '食品饮料', 'level': 1},
                        {'code': '801130', 'name': '纺织服装', 'level': 1},
                        {'code': '801140', 'name': '轻工制造', 'level': 1},
                        {'code': '801150', 'name': '医药生物', 'level': 1},
                        {'code': '801160', 'name': '公用事业', 'level': 1},
                        {'code': '801170', 'name': '交通运输', 'level': 1},
                        {'code': '801180', 'name': '房地产', 'level': 1},
                        {'code': '801200', 'name': '商业贸易', 'level': 1},
                        {'code': '801210', 'name': '休闲服务', 'level': 1},
                        {'code': '801230', 'name': '综合', 'level': 1},
                        {'code': '801710', 'name': '建筑材料', 'level': 1},
                        {'code': '801720', 'name': '建筑装饰', 'level': 1},
                        {'code': '801730', 'name': '电气设备', 'level': 1},
                        {'code': '801740', 'name': '国防军工', 'level': 1},
                        {'code': '801750', 'name': '计算机', 'level': 1},
                        {'code': '801760', 'name': '传媒', 'level': 1},
                        {'code': '801770', 'name': '通信', 'level': 1},
                        {'code': '801780', 'name': '银行', 'level': 1},
                        {'code': '801790', 'name': '非银金融', 'level': 1},
                        {'code': '801880', 'name': '汽车', 'level': 1},
                        {'code': '801890', 'name': '机械设备', 'level': 1}
                    ]
                    result[0] = pd.DataFrame(sw_industries)

            # 启动线程
            thread = threading.Thread(target=fetch_sw_industry_list)
            thread.daemon = True
            thread.start()

            # 等待10秒
            thread.join(timeout=10)

            if thread.is_alive():
                logger.warning(f"⚠️ AKShare申万行业分类获取超时（10秒）")
                raise Exception(f"申万行业分类获取超时（10秒）")
            elif exception[0]:
                raise exception[0]
            else:
                data = result[0]

            if data is not None and not data.empty:
                logger.info(f"✅ AKShare申万行业分类获取成功: {len(data)}个行业")
                return data
            else:
                logger.warning(f"⚠️ AKShare申万行业分类数据为空")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取申万行业分类失败: {e}")
            return None

    def get_sw_industry_constituents(self, industry_code: str) -> Optional[pd.DataFrame]:
        """
        获取申万行业成分股数据（基于AkShare官方API）
        
        Args:
            industry_code: 申万行业代码（如：801010）
            
        Returns:
            pd.DataFrame: 申万行业成分股数据
        """
        if not self.connected:
            logger.error(f"❌ AKShare未连接，无法获取申万行业成分股数据")
            return None

        try:
            logger.info(f"📊 AKShare获取申万行业成分股数据: {industry_code}")

            # 使用线程超时包装
            import threading
            result = [None]
            exception = [None]

            def fetch_sw_constituents():
                try:
                    # 使用AkShare官方API获取申万三级行业成分股
                    result[0] = self.ak.sw_index_third_cons(symbol=industry_code)
                except Exception as e:
                    exception[0] = e

            # 启动线程
            thread = threading.Thread(target=fetch_sw_constituents)
            thread.daemon = True
            thread.start()

            # 等待60秒
            thread.join(timeout=60)

            if thread.is_alive():
                # 超时了
                logger.warning(f"⚠️ AKShare申万行业成分股获取超时（60秒）: {industry_code}")
                raise Exception(f"申万行业成分股获取超时（60秒）: {industry_code}")
            elif exception[0]:
                # 有异常
                raise exception[0]
            else:
                # 成功
                data = result[0]

            if data is not None and not data.empty:
                logger.info(f"✅ AKShare申万行业成分股获取成功: {industry_code}, {len(data)}条记录")
                return data
            else:
                logger.warning(f"⚠️ AKShare申万行业成分股数据为空: {industry_code}")
                return None

        except Exception as e:
            logger.error(f"❌ AKShare获取申万行业成分股失败: {industry_code}, 错误: {e}")
            return None

def get_akshare_provider() -> AKShareProvider:
    """获取AKShare提供器实例"""
    return AKShareProvider()


# 便捷函数
def get_hk_stock_data_akshare(symbol: str, start_date: str = None, end_date: str = None) -> str:
    """
    使用AKShare获取港股数据的便捷函数

    Args:
        symbol: 港股代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的港股数据
    """
    try:
        provider = get_akshare_provider()
        data = provider.get_hk_stock_data(symbol, start_date, end_date)

        if data is not None and not data.empty:
            return format_hk_stock_data_akshare(symbol, data, start_date, end_date)
        else:
            return f"❌ 无法获取港股 {symbol} 的AKShare数据"

    except Exception as e:
        return f"❌ AKShare港股数据获取失败: {e}"


def get_hk_stock_info_akshare(symbol: str) -> Dict[str, Any]:
    """
    使用AKShare获取港股信息的便捷函数

    Args:
        symbol: 港股代码

    Returns:
        Dict: 港股信息
    """
    try:
        provider = get_akshare_provider()
        return provider.get_hk_stock_info(symbol)
    except Exception as e:
        return {
            'symbol': symbol,
            'name': f'港股{symbol}',
            'currency': 'HKD',
            'exchange': 'HKG',
            'source': 'akshare_error',
            'error': str(e)
        }


def format_hk_stock_data_akshare(symbol: str, data: pd.DataFrame, start_date: str, end_date: str) -> str:
    """
    格式化AKShare港股数据为文本格式

    Args:
        symbol: 股票代码
        data: 股票数据DataFrame
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 格式化的股票数据文本
    """
    if data is None or data.empty:
        return f"❌ 无法获取港股 {symbol} 的AKShare数据"

    try:
        # 获取股票基本信息（允许失败）
        stock_name = f'港股{symbol}'  # 默认名称
        try:
            provider = get_akshare_provider()
            stock_info = provider.get_hk_stock_info(symbol)
            stock_name = stock_info.get('name', f'港股{symbol}')
            logger.info(f"✅ 港股信息获取成功: {stock_name}")
        except Exception as info_error:
            logger.error(f"⚠️ 港股信息获取失败，使用默认信息: {info_error}")
            # 继续处理，使用默认信息

        # 计算统计信息
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
        price_change_pct = (price_change / data['Close'].iloc[0]) * 100

        avg_volume = data['Volume'].mean() if 'Volume' in data.columns else 0
        max_price = data['High'].max()
        min_price = data['Low'].min()

        # 格式化输出
        formatted_text = f"""
🇭🇰 港股数据报告 (AKShare)
================

股票信息:
- 代码: {symbol}
- 名称: {stock_name}
- 货币: 港币 (HKD)
- 交易所: 香港交易所 (HKG)

价格信息:
- 最新价格: HK${latest_price:.2f}
- 期间涨跌: HK${price_change:+.2f} ({price_change_pct:+.2f}%)
- 期间最高: HK${max_price:.2f}
- 期间最低: HK${min_price:.2f}

交易信息:
- 数据期间: {start_date} 至 {end_date}
- 交易天数: {len(data)}天
- 平均成交量: {avg_volume:,.0f}股

最近5个交易日:
"""

        # 添加最近5天的数据
        recent_data = data.tail(5)
        for _, row in recent_data.iterrows():
            date = row['Date'].strftime('%Y-%m-%d') if 'Date' in row else row.name.strftime('%Y-%m-%d')
            volume = row.get('Volume', 0)
            formatted_text += f"- {date}: 开盘HK${row['Open']:.2f}, 收盘HK${row['Close']:.2f}, 成交量{volume:,.0f}\n"

        formatted_text += f"\n数据来源: AKShare (港股)\n"

        return formatted_text

    except Exception as e:
        logger.error(f"❌ 格式化AKShare港股数据失败: {e}")
        return f"❌ AKShare港股数据格式化失败: {symbol}"


def get_stock_news_em(symbol: str) -> pd.DataFrame:
    """
    使用AKShare获取东方财富个股新闻

    Args:
        symbol: 股票代码，如 "600000" 或 "300059"

    Returns:
        pd.DataFrame: 包含新闻标题、内容、日期和链接的DataFrame
    """
    start_time = datetime.now()
    logger.info(f"[东方财富新闻] 开始获取股票 {symbol} 的东方财富新闻数据")
    
    try:
        provider = get_akshare_provider()
        if not provider.connected:
            logger.error(f"[东方财富新闻] ❌ AKShare未连接，无法获取东方财富新闻")
            return pd.DataFrame()

        logger.info(f"[东方财富新闻] 📰 准备调用AKShare API获取个股新闻: {symbol}")

        # 使用线程超时包装（兼容Windows）
        import threading
        import time

        result = [None]
        exception = [None]

        def fetch_news():
            try:
                logger.debug(f"[东方财富新闻] 线程开始执行 stock_news_em API调用: {symbol}")
                thread_start = time.time()
                result[0] = provider.ak.stock_news_em(symbol=symbol)
                thread_end = time.time()
                logger.debug(f"[东方财富新闻] 线程执行完成，耗时: {thread_end - thread_start:.2f}秒")
            except Exception as e:
                logger.error(f"[东方财富新闻] 线程执行异常: {e}")
                exception[0] = e

        # 启动线程
        thread = threading.Thread(target=fetch_news)
        thread.daemon = True
        logger.debug(f"[东方财富新闻] 启动线程获取新闻数据")
        thread.start()

        # 等待30秒
        logger.debug(f"[东方财富新闻] 等待线程完成，最长等待30秒")
        thread.join(timeout=30)

        if thread.is_alive():
            # 超时了
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"[东方财富新闻] ⚠️ 获取超时（30秒）: {symbol}，总耗时: {elapsed_time:.2f}秒")
            raise Exception(f"东方财富个股新闻获取超时（30秒）: {symbol}")
        elif exception[0]:
            # 有异常
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"[东方财富新闻] ❌ API调用异常: {exception[0]}，总耗时: {elapsed_time:.2f}秒")
            raise exception[0]
        else:
            # 成功
            news_df = result[0]

        if news_df is not None and not news_df.empty:
            news_count = len(news_df)
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # 记录一些新闻标题示例
            sample_titles = [row.get('标题', '无标题') for _, row in news_df.head(3).iterrows()]
            logger.info(f"[东方财富新闻] 新闻标题示例: {', '.join(sample_titles)}")
            
            logger.info(f"[东方财富新闻] ✅ 获取成功: {symbol}, 共{news_count}条记录，耗时: {elapsed_time:.2f}秒")
            return news_df
        else:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"[东方财富新闻] ⚠️ 数据为空: {symbol}，API返回成功但无数据，耗时: {elapsed_time:.2f}秒")
            return pd.DataFrame()

    except Exception as e:
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"[东方财富新闻] ❌ 获取失败: {symbol}, 错误: {e}, 耗时: {elapsed_time:.2f}秒")
        return pd.DataFrame()


# 申万指数数据便捷函数

def get_sw_index_hist_akshare(symbol: str, period: str = "day", 
                             start_date: str = None, end_date: str = None,
                             use_cache: bool = True) -> str:
    """
    使用AKShare获取申万指数历史数据的便捷函数（集成缓存）
    
    Args:
        symbol: 申万指数代码（如：801010, 801193）
        period: 数据周期（"day", "week", "month"）
        start_date: 开始日期（格式：YYYY-MM-DD）
        end_date: 结束日期（格式：YYYY-MM-DD）
        use_cache: 是否使用缓存
    
    Returns:
        str: 格式化的申万指数数据
    """
    try:
        from .cache_manager import get_cache
        
        cache = get_cache() if use_cache else None
        cached_data = None
        
        # 检查缓存
        if cache and use_cache:
            cache_key = cache.find_cached_sw_index_data(
                symbol=symbol, 
                start_date=start_date, 
                end_date=end_date,
                data_source='akshare'
            )
            if cache_key:
                cached_data = cache.load_sw_index_data(cache_key)
        
        # 如果有缓存数据，使用缓存
        if cached_data is not None:
            if isinstance(cached_data, pd.DataFrame):
                return format_sw_index_data_akshare(symbol, cached_data, period, start_date, end_date)
            else:
                return cached_data  # 如果是字符串格式，直接返回
        
        # 否则从AKShare获取新数据
        provider = get_akshare_provider()
        data = provider.get_sw_index_hist(symbol, period, start_date, end_date)
        
        if data is not None and not data.empty:
            # 保存到缓存
            if cache and use_cache:
                cache.save_sw_index_data(
                    symbol=symbol,
                    data=data,
                    start_date=start_date,
                    end_date=end_date,
                    data_source='akshare'
                )
            
            return format_sw_index_data_akshare(symbol, data, period, start_date, end_date)
        else:
            return f"❌ 无法获取申万指数 {symbol} 的AKShare数据"
    
    except Exception as e:
        logger.error(f"❌ AKShare申万指数数据获取失败: {e}")
        return f"❌ AKShare申万指数数据获取失败: {e}"


def get_sw_components_akshare(symbol: str, use_cache: bool = True) -> str:
    """
    使用AKShare获取申万指数成分股的便捷函数（集成缓存）
    
    Args:
        symbol: 申万指数代码（如：801010, 801193）
        use_cache: 是否使用缓存
    
    Returns:
        str: 格式化的申万指数成分股数据
    """
    try:
        from .cache_manager import get_cache
        
        cache = get_cache() if use_cache else None
        cached_data = None
        
        # 检查缓存
        if cache and use_cache:
            cache_key = cache.find_cached_sw_industry_data(
                data_type='sw_components_data',
                data_key=symbol,
                data_source='akshare'
            )
            if cache_key:
                cached_data = cache.load_sw_industry_data(cache_key)
        
        # 如果有缓存数据，使用缓存
        if cached_data is not None:
            if isinstance(cached_data, pd.DataFrame):
                return format_sw_components_data_akshare(symbol, cached_data)
            else:
                return cached_data  # 如果是字符串格式，直接返回
        
        # 否则从AKShare获取新数据
        provider = get_akshare_provider()
        data = provider.get_sw_components(symbol)
        
        if data is not None and not data.empty:
            # 保存到缓存
            if cache and use_cache:
                cache.save_sw_industry_data(
                    data_type='sw_components_data',
                    data=data,
                    data_key=symbol,
                    data_source='akshare'
                )
            
            return format_sw_components_data_akshare(symbol, data)
        else:
            return f"❌ 无法获取申万指数 {symbol} 成分股的AKShare数据"
    
    except Exception as e:
        logger.error(f"❌ AKShare申万指数成分股数据获取失败: {e}")
        return f"❌ AKShare申万指数成分股数据获取失败: {e}"


def format_sw_index_data_akshare(symbol: str, data: pd.DataFrame, period: str, 
                                start_date: str, end_date: str) -> str:
    """
    格式化AKShare申万指数数据为文本格式
    
    Args:
        symbol: 申万指数代码
        data: 申万指数数据DataFrame
        period: 数据周期
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        str: 格式化的申万指数数据文本
    """
    if data is None or data.empty:
        return f"❌ 无法获取申万指数 {symbol} 的AKShare数据"
    
    try:
        # 获取指数基本信息（根据代码映射）
        sw_industry_map = {
            '801010': '农林牧渔', '801020': '采掘', '801030': '化工', '801040': '钢铁',
            '801050': '有色金属', '801080': '电子', '801110': '家用电器', '801120': '食品饮料',
            '801130': '纺织服装', '801140': '轻工制造', '801150': '医药生物', '801160': '公用事业',
            '801170': '交通运输', '801180': '房地产', '801200': '商业贸易', '801210': '休闲服务',
            '801230': '综合', '801710': '建筑材料', '801720': '建筑装饰', '801730': '电气设备',
            '801740': '国防军工', '801750': '计算机', '801760': '传媒', '801770': '通信',
            '801780': '银行', '801790': '非银金融', '801880': '汽车', '801890': '机械设备'
        }
        
        index_name = sw_industry_map.get(symbol, f'申万指数{symbol}')
        
        # 计算统计信息
        latest_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
        price_change_pct = (price_change / data['Close'].iloc[0]) * 100
        
        avg_volume = data['Volume'].mean() if 'Volume' in data.columns else 0
        max_price = data['High'].max()
        min_price = data['Low'].min()
        
        # 格式化输出
        period_desc = {"day": "日线", "week": "周线", "month": "月线"}.get(period, period)
        
        formatted_text = f"""
📊 申万指数数据报告 (AKShare)
================

指数信息:
- 代码: {symbol}
- 名称: {index_name}
- 分类: 申万一级行业指数
- 数据周期: {period_desc}

价格信息:
- 最新价格: {latest_price:.3f}点
- 期间涨跌: {price_change:+.3f}点 ({price_change_pct:+.2f}%)
- 期间最高: {max_price:.3f}点
- 期间最低: {min_price:.3f}点

交易信息:
- 数据期间: {start_date or '历史数据'} 至 {end_date or '最新'}
- 数据条数: {len(data)}条
- 平均成交量: {avg_volume:,.0f}手

最近5个交易周期:
"""
        
        # 添加最近5个周期的数据
        recent_data = data.tail(5)
        for _, row in recent_data.iterrows():
            date = row['Date'].strftime('%Y-%m-%d') if 'Date' in row else row.name.strftime('%Y-%m-%d')
            volume = row.get('Volume', 0)
            formatted_text += f"- {date}: 开盘{row['Open']:.3f}, 收盘{row['Close']:.3f}, 成交量{volume:,.0f}\n"
        
        formatted_text += f"\n数据来源: AKShare (申万指数)\n"
        
        return formatted_text
    
    except Exception as e:
        logger.error(f"❌ 格式化AKShare申万指数数据失败: {e}")
        return f"❌ AKShare申万指数数据格式化失败: {symbol}"


def format_sw_components_data_akshare(symbol: str, data: pd.DataFrame) -> str:
    """
    格式化AKShare申万指数成分股数据为文本格式
    
    Args:
        symbol: 申万指数代码
        data: 申万指数成分股数据DataFrame
    
    Returns:
        str: 格式化的申万指数成分股数据文本
    """
    if data is None or data.empty:
        return f"❌ 无法获取申万指数 {symbol} 成分股的AKShare数据"
    
    try:
        # 获取指数基本信息
        sw_industry_map = {
            '801010': '农林牧渔', '801020': '采掘', '801030': '化工', '801040': '钢铁',
            '801050': '有色金属', '801080': '电子', '801110': '家用电器', '801120': '食品饮料',
            '801130': '纺织服装', '801140': '轻工制造', '801150': '医药生物', '801160': '公用事业',
            '801170': '交通运输', '801180': '房地产', '801200': '商业贸易', '801210': '休闲服务',
            '801230': '综合', '801710': '建筑材料', '801720': '建筑装饰', '801730': '电气设备',
            '801740': '国防军工', '801750': '计算机', '801760': '传媒', '801770': '通信',
            '801780': '银行', '801790': '非银金融', '801880': '汽车', '801890': '机械设备'
        }
        
        index_name = sw_industry_map.get(symbol, f'申万指数{symbol}')
        
        # 格式化输出
        formatted_text = f"""
📈 申万指数成分股报告 (AKShare)
================

指数信息:
- 代码: {symbol}
- 名称: {index_name}
- 成分股数量: {len(data)}只

权重分布:
- 前10大权重股占比: {data.head(10)['Weight'].sum() if 'Weight' in data.columns else 'N/A'}%
- 平均权重: {data['Weight'].mean():.3f}% (如果有权重数据)

前20大成分股:
"""
        
        # 添加前20只股票的详细信息
        top_stocks = data.head(20)
        for _, row in top_stocks.iterrows():
            rank = row.get('Rank', '?')
            code = row.get('Code', '?')
            name = row.get('Name', '?')
            weight = row.get('Weight', 0)
            date = row.get('Date', '?')
            
            if weight > 0:
                formatted_text += f"- {rank}. {code} {name}: {weight:.3f}% (计入日期: {date})\n"
            else:
                formatted_text += f"- {rank}. {code} {name} (计入日期: {date})\n"
        
        if len(data) > 20:
            formatted_text += f"\n... 还有 {len(data) - 20} 只成分股\n"
        
        formatted_text += f"\n数据来源: AKShare (申万指数成分股)\n"
        
        return formatted_text
    
    except Exception as e:
        logger.error(f"❌ 格式化AKShare申万指数成分股数据失败: {e}")
        return f"❌ AKShare申万指数成分股数据格式化失败: {symbol}"


# 申万行业数据便捷函数（基于AkShare优先策略）

def get_sw_industry_list_akshare(use_cache: bool = True) -> str:
    """
    使用AKShare获取申万行业分类列表的便捷函数（集成缓存）
    
    Args:
        use_cache: 是否使用缓存
        
    Returns:
        str: 格式化的申万行业分类列表
    """
    try:
        from .cache_manager import CacheManager
        cache = CacheManager()
        
        # 检查缓存
        if use_cache:
            cache_key = cache.find_cached_sw_industry_data(
                data_type='sw_industry_list',
                symbol='ALL'
            )
            
            if cache_key:
                cached_data = cache.load_sw_industry_data(cache_key)
                if cached_data is not None and not cached_data.empty:
                    logger.info(f"🎯 使用缓存的申万行业分类列表")
                    return format_sw_industry_list_akshare(cached_data)
        
        # 获取新数据
        provider = AKShareProvider()
        data = provider.get_sw_industry_list()
        
        if data is not None and not data.empty:
            # 保存到缓存
            if use_cache:
                cache.save_sw_industry_data(
                    data_type='sw_industry_list',
                    symbol='ALL',
                    data=data
                )
            
            return format_sw_industry_list_akshare(data)
        else:
            return "❌ 无法获取申万行业分类的AKShare数据"
            
    except Exception as e:
        logger.error(f"❌ AKShare申万行业分类获取失败: {e}")
        return f"❌ AKShare申万行业分类获取失败: {e}"


def get_sw_industry_constituents_akshare(industry_code: str, use_cache: bool = True) -> str:
    """
    使用AKShare获取申万行业成分股的便捷函数（集成缓存）
    
    Args:
        industry_code: 申万行业代码（如：801010）
        use_cache: 是否使用缓存
        
    Returns:
        str: 格式化的申万行业成分股数据
    """
    try:
        from .cache_manager import CacheManager
        cache = CacheManager()
        
        # 检查缓存
        if use_cache:
            cache_key = cache.find_cached_sw_industry_data(
                data_type='sw_constituents_data',
                symbol=industry_code
            )
            
            if cache_key:
                cached_data = cache.load_sw_industry_data(cache_key)
                if cached_data is not None and not cached_data.empty:
                    logger.info(f"🎯 使用缓存的申万行业成分股数据: {industry_code}")
                    return format_sw_industry_constituents_akshare(industry_code, cached_data)
        
        # 获取新数据
        provider = AKShareProvider()
        data = provider.get_sw_industry_constituents(industry_code)
        
        if data is not None and not data.empty:
            # 保存到缓存
            if use_cache:
                cache.save_sw_industry_data(
                    data_type='sw_constituents_data',
                    symbol=industry_code,
                    data=data
                )
            
            return format_sw_industry_constituents_akshare(industry_code, data)
        else:
            return f"❌ 无法获取申万行业 {industry_code} 成分股的AKShare数据"
            
    except Exception as e:
        logger.error(f"❌ AKShare申万行业成分股获取失败: {e}")
        return f"❌ AKShare申万行业成分股获取失败: {e}"


def format_sw_industry_list_akshare(data: pd.DataFrame) -> str:
    """
    格式化AKShare申万行业分类列表为文本格式
    
    Args:
        data: 申万行业分类数据DataFrame
        
    Returns:
        str: 格式化的申万行业分类列表文本
    """
    if data is None or data.empty:
        return "❌ 无法获取申万行业分类的AKShare数据"
    
    try:
        formatted_text = f"""
📊 申万行业分类列表 (AKShare)
{'='*50}

"""      
        
        # 添加行业分类统计信息
        formatted_text += f"📈 行业分类统计:\n"
        formatted_text += f"- 总行业数量: {len(data)}\n"
        
        # 检查数据列名并标准化
        data_columns = list(data.columns)
        code_col = next((col for col in data_columns if '代码' in col or 'code' in col.lower()), None)
        name_col = next((col for col in data_columns if '名称' in col or 'name' in col.lower()), None)
        count_col = next((col for col in data_columns if '成份' in col or '个数' in col), None)
        pe_col = next((col for col in data_columns if '市盈率' in col), None)
        
        if code_col and name_col:
            formatted_text += f"\n📋 行业详细列表:\n"
            formatted_text += f"{'行业代码':<10} {'行业名称':<20} {'成份数':<8}"
            
            if pe_col:
                formatted_text += f" {'市盈率':<10}"
            formatted_text += "\n" + "-"*60 + "\n"
            
            for _, row in data.head(20).iterrows():  # 显示前20个行业
                code = str(row[code_col]) if code_col else 'N/A'
                name = str(row[name_col]) if name_col else 'N/A'
                count = str(row[count_col]) if count_col and pd.notna(row[count_col]) else 'N/A'
                
                formatted_text += f"{code:<10} {name:<20} {count:<8}"
                
                if pe_col and pd.notna(row[pe_col]):
                    pe_value = f"{row[pe_col]:.2f}" if isinstance(row[pe_col], (int, float)) else str(row[pe_col])
                    formatted_text += f" {pe_value:<10}"
                    
                formatted_text += "\n"
                
            if len(data) > 20:
                formatted_text += f"... (显示前20个，共{len(data)}个行业)\n"
        else:
            # 如果列名不匹配，显示原始数据结构
            formatted_text += f"\n📋 数据结构:\n"
            formatted_text += f"列名: {', '.join(data_columns)}\n"
            formatted_text += f"\n前5行数据:\n{data.head().to_string()}\n"
            
        formatted_text += f"\n数据来源: AKShare (申万行业分类)\n"
        formatted_text += f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"❌ 格式化AKShare申万行业分类数据失败: {e}")
        return f"❌ AKShare申万行业分类数据格式化失败"


def format_sw_industry_constituents_akshare(industry_code: str, data: pd.DataFrame) -> str:
    """
    格式化AKShare申万行业成分股数据为文本格式
    
    Args:
        industry_code: 申万行业代码
        data: 申万行业成分股数据DataFrame
        
    Returns:
        str: 格式化的申万行业成分股数据文本
    """
    if data is None or data.empty:
        return f"❌ 无法获取申万行业 {industry_code} 成分股的AKShare数据"
    
    try:
        # 获取行业名称
        industry_name = "未知行业"
        if '申万3级' in data.columns and not data.empty:
            industry_name = data.iloc[0]['申万3级']
        elif '申万2级' in data.columns and not data.empty:
            industry_name = data.iloc[0]['申万2级']
        elif '申万1级' in data.columns and not data.empty:
            industry_name = data.iloc[0]['申万1级']
            
        formatted_text = f"""
📈 申万行业成分股报告 (AKShare)
{'='*50}

📊 行业信息:
- 行业代码: {industry_code}
- 行业名称: {industry_name}
- 成分股数量: {len(data)}

"""      
        
        # 添加成分股列表
        if not data.empty:
            formatted_text += f"📋 主要成分股（前15只）:\n"
            formatted_text += f"{'股票代码':<10} {'股票名称':<15} {'价格':<8} {'市值':<12} {'市盈率':<8}\n"
            formatted_text += "-"*60 + "\n"
            
            for _, row in data.head(15).iterrows():
                code = str(row.get('股票代码', 'N/A'))
                name = str(row.get('股票简称', 'N/A'))[:12]  # 限制长度
                price = f"{row.get('价格', 0):.2f}" if pd.notna(row.get('价格')) else 'N/A'
                market_cap = f"{row.get('市值', 0):.0f}亿" if pd.notna(row.get('市值')) else 'N/A'
                pe_ratio = f"{row.get('市盈率', 0):.2f}" if pd.notna(row.get('市盈率')) else 'N/A'
                
                formatted_text += f"{code:<10} {name:<15} {price:<8} {market_cap:<12} {pe_ratio:<8}\n"
            
            if len(data) > 15:
                formatted_text += f"... (显示前15只，共{len(data)}只成分股)\n"
                
            # 添加行业统计信息
            if '市盈率' in data.columns:
                avg_pe = data['市盈率'].dropna().mean()
                formatted_text += f"\n📊 行业统计:\n"
                formatted_text += f"- 平均市盈率: {avg_pe:.2f}\n"
                
            if '市值' in data.columns:
                total_market_cap = data['市值'].dropna().sum()
                formatted_text += f"- 总市值: {total_market_cap:.0f}亿元\n"
            
        formatted_text += f"\n数据来源: AKShare (申万行业成分股)\n"
        formatted_text += f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"❌ 格式化AKShare申万行业成分股数据失败: {e}")
        return f"❌ AKShare申万行业成分股数据格式化失败: {industry_code}"
