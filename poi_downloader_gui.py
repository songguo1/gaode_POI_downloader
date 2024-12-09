import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import pandas as pd
import time
from typing import List, Dict
from threading import Thread
import os

class POIDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("高德地图 POI 下载工具")
        self.root.geometry("600x400")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # API密钥输入
        ttk.Label(self.main_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key = ttk.Entry(self.main_frame, width=50)
        self.api_key.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 关键词输入
        ttk.Label(self.main_frame, text="搜索关键词:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.keywords = ttk.Entry(self.main_frame, width=50)
        self.keywords.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 城市输入
        ttk.Label(self.main_frame, text="城市名称:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.city = ttk.Entry(self.main_frame, width=50)
        self.city.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 保存位置选择
        ttk.Label(self.main_frame, text="保存位置:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.save_path = ttk.Entry(self.main_frame, width=40)
        self.save_path.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        self.save_path.insert(0, os.getcwd())  # 默认为当前目录
        
        self.browse_btn = ttk.Button(self.main_frame, text="浏览", command=self.browse_path)
        self.browse_btn.grid(row=3, column=2, padx=5, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.main_frame, length=400, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 状态显示
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 下载按钮
        self.download_btn = ttk.Button(self.main_frame, text="开始下载", command=self.start_download)
        self.download_btn.grid(row=6, column=1, pady=20)
        
        # 日志文本框
        self.log_text = tk.Text(self.main_frame, height=10, width=50)
        self.log_text.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.downloader = None

    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        
    def browse_path(self):
        """选择保存位置"""
        directory = filedialog.askdirectory()
        if directory:
            self.save_path.delete(0, tk.END)
            self.save_path.insert(0, directory)
    
    def start_download(self):
        api_key = self.api_key.get().strip()
        keywords = self.keywords.get().strip()
        city = self.city.get().strip()
        save_dir = self.save_path.get().strip()
        
        if not all([api_key, keywords, city, save_dir]):
            messagebox.showerror("错误", "请填写所有必要信息！")
            return
            
        if not os.path.exists(save_dir):
            messagebox.showerror("错误", "保存位置不存在！")
            return
            
        self.download_btn.config(state='disabled')
        self.progress.start()
        self.status_var.set("正在下载...")
        
        # 在新线��中执行下载
        Thread(target=self.download_poi, args=(api_key, keywords, city, save_dir)).start()
        
    def download_poi(self, api_key: str, keywords: str, city: str, save_dir: str):
        try:
            self.downloader = GaodePOIDownloader(api_key)
            pois = self.downloader.get_all_pois(keywords, city)
            
            if pois:
                output_file = os.path.join(save_dir, f"{city}_{keywords}_pois.csv")
                self.downloader.save_to_csv(pois, output_file)
                self.log(f"下载完成！共获取到 {len(pois)} 条数据")
                self.status_var.set(f"下载完成！数据已保存到: {output_file}")
            else:
                self.log("未找到相关数据")
                self.status_var.set("下载失败：未找到相关数据")
                
        except Exception as e:
            self.log(f"发生错误: {str(e)}")
            self.status_var.set("下载失败")
            messagebox.showerror("错误", str(e))
            
        finally:
            self.progress.stop()
            self.download_btn.config(state='normal')

class GaodePOIDownloader:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/place/text"
        
    def search_poi(self, keywords: str, city: str, page: int = 1) -> Dict:
        params = {
            'key': self.api_key,
            'keywords': keywords,
            'city': city,
            'offset': 20,
            'page': page,
            'extensions': 'all'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def get_all_pois(self, keywords: str, city: str) -> List[Dict]:
        all_pois = []
        page = 1
        
        while True:
            result = self.search_poi(keywords, city, page)
            
            if not result or result.get('status') != '1':
                print(f"获取第{page}页数据失败")
                break
                
            pois = result.get('pois', [])
            if not pois:
                break
                
            all_pois.extend(pois)
            
            if len(pois) < 20:
                break
                
            page += 1
            time.sleep(0.5)
            
        return all_pois

    def save_to_csv(self, pois: List[Dict], output_file: str):
        """
        将POI数据保存为CSV文件，只保存指定字段
        """
        if not pois:
            print("没有数据可保存")
            return
            
        # 提取需要的字段
        processed_pois = []
        for poi in pois:
            processed_poi = {
                'name': poi.get('name', ''),
                'longitude': poi.get('location', '').split(',')[0] if poi.get('location') else '',
                'latitude': poi.get('location', '').split(',')[1] if poi.get('location') else '',
                'type': poi.get('type', ''),
                'province': poi.get('pname', ''),
                'city': poi.get('cityname', ''),
                'district': poi.get('adname', ''),
                'address': poi.get('address', '')
            }
            processed_pois.append(processed_poi)
            
        # 创建DataFrame并设置中文列名
        df = pd.DataFrame(processed_pois)
        df.columns = [
            '名称',
            '经度',
            '纬度',
            '类型',
            '省份',
            '城市',
            '区县',
            '详细地址'
        ]
        
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

def main():
    root = tk.Tk()
    app = POIDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 