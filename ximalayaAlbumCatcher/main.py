import os
from libs.ximalayaseleniumcrawler import XimalayaSeleniumCrawler


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
