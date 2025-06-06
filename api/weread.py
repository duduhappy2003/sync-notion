# 封装微信api的调用
from http.cookies import SimpleCookie
from requests.utils import cookiejar_from_dict
import requests


class WeReadAPI:
    """微信读书API"""

    # 全量书籍笔记信息列表
    WEREAD_NOTEBOOKS_URL = "https://weread.qq.com/api/user/notebook"

    # 章节信息列表
    WEREAD_CHAPTER_INFO = "https://weread.qq.com/web/book/chapterInfos"

    # 书籍划线
    WEREAD_BOOKMARKLIST_URL = "https://weread.qq.com/web/book/bookmarklist"

    # 获取笔记列表，包括笔记、推荐总结
    WEREAD_REVIEW_LIST_URL = "https://weread.qq.com/web/review/list"

    # 数据详情
    WEREAD_BOOK_INFO = "https://weread.qq.com/web/book/info"

    # 读取进度等
    WEREAD_READ_INFO_URL = "https://weread.qq.com/web/book/readinfo"

    WEREAD_URL = "https://weread.qq.com/"

    def __init__(self, cookie):
        session = requests.Session()
        session.cookies = self._parse_cookie(cookie)
        session.get(self.WEREAD_URL)
        self.session = session

    def _parse_cookie(self, cookie_string):
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        cookies_dict = {}
        cookiejar = None
        for key, morsel in cookie.items():
            cookies_dict[key] = morsel.value
            cookiejar = cookiejar_from_dict(
                cookies_dict, cookiejar=None, overwrite=True
            )
        return cookiejar

    def get_notebooklist(self):
        """全量书籍笔记信息列表，仅包括笔记更新时间、数量等，不包括笔记明细"""
        r = self.session.get(self.WEREAD_NOTEBOOKS_URL)
        if r.ok:
            data = r.json()
            books = data.get("books")
            books.sort(
                key=lambda x: x["sort"]
            )  # 最近更新（划线、评语以及推荐都算更新）时间
            return books
        else:
            print(f"get notesbook failed: {r.text}")
            return []

    def get_chapter_list(self, bookId):
        """获取章节信息列表"""
        body = {"bookIds": [bookId]}
        r = self.session.post(self.WEREAD_CHAPTER_INFO, json=body)
        if (
            r.ok
            and "data" in r.json()
            and len(r.json()["data"]) == 1
            and "updated" in r.json()["data"][0]
        ):
            update = r.json()["data"][0]["updated"]
            # d = {item["chapterUid"]: item for item in update}
            return update
        else:
            print(r.text)
        return []

    def get_bookmark_list(self, bookId):
        """获取书籍划线列表"""
        params = dict(bookId=bookId)
        r = self.session.get(self.WEREAD_BOOKMARKLIST_URL, params=params)
        if r.ok:
            updated = r.json().get("updated")
            updated = sorted(
                updated,
                key=lambda x: (
                    x.get("chapterUid", 1),
                    int(x.get("range").split("-")[0]),
                ),
            )
            return r.json()["updated"]
        else:
            print("get bookmarklist failed: {r.text}")
        return []

    def get_review_list(self, bookId):
        """获取笔记列表，包括笔记评论、推荐总结"""
        params = dict(bookId=bookId, listType=11, mine=1, syncKey=0)
        r = self.session.get(self.WEREAD_REVIEW_LIST_URL, params=params)
        if r.ok:
            reviews = r.json().get("reviews")
            # 总结
            summary = list(filter(lambda x: x.get("review").get("type") == 4, reviews))
            # 笔记（评语）
            reviews = list(filter(lambda x: x.get("review").get("type") == 1, reviews))
            reviews = list(map(lambda x: x.get("review"), reviews))
            reviews = list(map(lambda x: {**x, "markText": x.pop("content")}, reviews))
            return summary, reviews
        else:
            print(r.text)
            return [], []

    def get_bookinfo(self, bookId: str) -> list:
        """获取书的详情"""
        params = dict(bookId=bookId)
        r = self.session.get(self.WEREAD_BOOK_INFO, params=params)
        isbn = ""
        rating = 0
        category = ""
        intro = ""

        if r.ok:
            data = r.json()
            isbn = data["isbn"]
            rating = data["newRating"] / 1000
            category = data.get("category", "")
            intro = data.get("intro", "")

        return (isbn, rating, category, intro)

    def get_read_info(self, bookId):
        """获取书籍的进度"""
        params = dict(
            bookId=bookId, readingDetail=1, readingBookIndex=1, finishedDate=1
        )
        r = self.session.get(self.WEREAD_READ_INFO_URL, params=params)
        if r.ok:
            return r.json()
        return {}


def str_reading_time(reading_time: int):
    "convert reading time to str"
    format_time = ""
    hour = reading_time // 3600
    if hour > 0:
        format_time += f"{hour}时"
    minutes = reading_time % 3600 // 60
    if minutes > 0:
        format_time += f"{minutes}分"
    return format_time
