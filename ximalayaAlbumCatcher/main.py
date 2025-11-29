from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os


class XimalayaSeleniumCrawler:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        # print("="*100)
        # print("请在一会后弹出的Chrome窗口上登录您的喜马拉雅帐号，忽略Chrome对您的“”警告。")
        # print("在登录完成后，请返回此窗口并按任意键继续。")
        # print("="*100)
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            print("Chrome驱动初始化成功。")
        except Exception as e:
            print(f"Chrome驱动初始化失败: {e}")
            raise
    
    def get_anchor_name(self, anchor_id):
        try:
            url = f'https://www.ximalaya.com/zhubo/{anchor_id}/'
            self.driver.get(url)
            time.sleep(3)
            selectors = [
                '.anchor-info__name',
                '.user-title',
                '.name',
                'h1',
                '.personal-header-name'
            ]
            anchor_name = f"主播_{anchor_id}"
            for selector in selectors:
                try:
                    name_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if name_element.text.strip():
                        anchor_name = name_element.text.strip()
                        print(f"获取到主播名称: {anchor_name}")
                        break
                except:
                    continue
            return anchor_name
        except Exception as e:
            print(f"获取主播名称失败: {e}")
            return f"主播_{anchor_id}"
    
    def get_albums_from_album_tab(self, anchor_id):
        albums = []
        try:
            anchor_name = self.get_anchor_name(anchor_id)
            url = f'https://www.ximalaya.com/zhubo/{anchor_id}/'
            print(f"正在访问主播主页: {url}")
            self.driver.get(url)
            time.sleep(5)
            print("正在点击专辑标签...")
            album_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '专辑')]"))
            )
            album_tab.click()
            time.sleep(3)
            albums = self.extract_all_albums(anchor_name)
        except Exception as e:
            print(f"获取专辑数据失败: {e}")
        return albums
    
    def extract_all_albums(self, anchor_name):
        albums = []
        previous_count = 0
        max_attempts = 100
        retryTimes = 0
        for attempt in range(max_attempts):
            print(f"第 {attempt + 1}/100 次尝试提取专辑数据...")
            retryTimes += 1
            current_albums = self.extract_albums_from_current_page(anchor_name)
            for album in current_albums:
                if album not in albums:
                    albums.append(album)
            print(f"当前已提取 {len(albums)} 个专辑。")
            if len(albums) == previous_count:
                if retryTimes < 3:
                    print(f"没有新专辑加载，正在第{retryTimes}次重试...")
                else:
                    print("3次没有新专辑加载，可能已加载完毕。")
                    break
            else:
                retryTimes = 0
            previous_count = len(albums)
            if not self.click_load_more():
                print("没有找到加载更多按钮，可能已加载完毕。")
                break
            time.sleep(2)
        print(f"最终共获取 {len(albums)} 个专辑。")
        return albums
    
    def extract_albums_from_current_page(self, anchor_name):
        albums = []
        try:
            album_containers = self.driver.find_elements(By.CSS_SELECTOR, '.anchor-user-album-box')
            print(f"找到 {len(album_containers)} 个专辑容器。")
            for container in album_containers:
                try:
                    album_info = self.extract_album_info(container, anchor_name)
                    if album_info:
                        albums.append(album_info)
                except Exception as e:
                    print(f"提取单个专辑信息失败: {e}")
                    continue
        except Exception as e:
            print(f"提取当前页面专辑失败: {e}")
        return albums
    
    def extract_album_info(self, container, anchor_name):
        try:
            title_element = container.find_element(By.CSS_SELECTOR, '.anchor-user-album-title')
            album_name = title_element.text.strip()
            album_url = title_element.get_attribute('href')
            album_id_match = re.search(r'/album/(\d+)', album_url)
            if not album_id_match:
                return None
            album_id = album_id_match.group(1)
            is_finished = False
            try:
                finished_icon = container.find_element(By.CSS_SELECTOR, '.xuicon-wanben')
                if finished_icon:
                    is_finished = True
            except:
                pass
            intro_element = container.find_element(By.CSS_SELECTOR, '.anchor-user-album-signature')
            album_intro = intro_element.text.strip()
            total_tracks = 0
            play_count = "0"
            try:
                tracks_element = container.find_element(By.XPATH, ".//div[contains(@class, 'anchor-user-album-counter')]//i[contains(@class, 'xuicon-sound-n')]/following-sibling::span")
                tracks_text = tracks_element.text
                tracks_match = re.search(r'(\d+)', tracks_text)
                if tracks_match:
                    total_tracks = int(tracks_match.group(1))
            except:
                pass
            try:
                play_element = container.find_element(By.XPATH, ".//div[contains(@class, 'anchor-user-album-counter')]//i[contains(@class, 'xuicon-erji1')]/following-sibling::span")
                play_text = play_element.text
                play_count = self.parse_play_count(play_text)
            except:
                pass
            return {
                'album_id': album_id,
                'album_name': album_name,
                'album_intro': album_intro,
                'is_finished': is_finished,
                'total_tracks': total_tracks,
                'play_count': play_count,
                'album_url': album_url,
                'author': anchor_name
            }
        except Exception as e:
            print(f"提取专辑信息失败: {e}")
            return None
    
    def parse_play_count(self, text):
        try:
            text = text.strip()
            if '万' in text:
                return text.strip()
            elif '亿' in text:
                return text.strip()
            else:
                return re.sub(r'[^\d]', '', text)
        except:
            return "--"
    
    def click_load_more(self):
        try:
            load_more_selectors = [
                "//span[contains(text(), '加载更多')]",
                "//button[contains(text(), '加载更多')]",
                "//a[contains(text(), '加载更多')]",
                "//div[contains(text(), '加载更多')]"
            ]
            
            for selector in load_more_selectors:
                try:
                    load_more_btn = self.driver.find_element(By.XPATH, selector)
                    if load_more_btn.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
                        time.sleep(1)
                        load_more_btn.click()
                        print("点击了加载更多按钮。")
                        return True
                except:
                    continue
            print("未找到可点击的加载更多按钮。")
            return False
        except Exception as e:
            print(f"点击加载更多按钮失败: {e}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭。")


def main():
    crawler = None
    try:
        crawler = XimalayaSeleniumCrawler()
        
        ids = [] #请在此处填写主播的ID，或是进行用户输入。
        all_albums = []
        for anchor_id in ids:
            if not anchor_id:
                print("主播ID失效或无效。")
                continue
            print(f"开始爬取主播 {anchor_id} 的专辑数据...")
            albums = crawler.get_albums_from_album_tab(anchor_id)
            if not albums:
                print("未找到专辑数据。")
            else:
                all_albums.extend(albums)
        print("=" * 100)
        finished, keeping = 0, 0
        for item in all_albums:
            if item['is_finished']:
                finished += 1
            else:
                keeping += 1
        print(f"\n共找到 {len(all_albums)} 个专辑，其中有 {finished} 本已完结，有 {keeping} 本正在连载。")
        print(f"\n专辑数据预览:")
        for i, album in enumerate(all_albums, 1):
            print(f"{f"{i}.":<4} {f"[{album['album_id']}]":<13} - {album['album_name']}")
            print(f"      简介: {album['album_intro'][:80]}{'...' if len(album['album_intro']) > 80 else ''}")
            print(f"      作者: {album['author']:<15} 状态: {'已完结' if album['is_finished'] else '连载中':<10} 总章节: {album['total_tracks']:<10} 播放量: {album['play_count']:<15}")
            print()
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        if crawler:
            crawler.close()


if __name__ == "__main__":
    print("正在初始化Chrome...")
    main()
    print("按任意键退出。")
    os.system("pause>nul")
