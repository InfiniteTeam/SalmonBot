from typing import Union, List, Tuple
import math

class Pager:
    def __init__(self, obj: Union[List, Tuple], perpage: int=1):
        if isinstance(perpage, int) and 0 < perpage:
            self.__perpage = perpage
        else:
            raise TypeError('페이지당 요소 최대 개수는 반드시 자연수여야합니다.')
        self.__obj = obj
        self.__page = 0
        self.__pageindexes = list(range(0, len(self.__obj)+1, self.__perpage))

    def next(self):
        if self.__page < len(self.__pageindexes):
            self.__page += 1
        else:
            raise StopIteration

    def prev(self):
        if self.__page > 0:
            self.__page -= 1
        else:
            raise StopIteration

    def setpage(self, page):
        if isinstance(page, int) and 0 <= page:
            if self.__page >= 0 and page < len(self.__pageindexes):
                self.__page = page
            else:
                raise IndexError('최대 페이지는 {}입니다.'.format(len(self.__pageindexes)-1))
        else:
            raise TypeError('페이지 번호는 반드시 0 또는 자연수여야합니다.')
    
    def now_pagenum(self):
        return self.__page

    def pages(self):
        return self.__pageindexes

    def get_thispage(self) -> list:
        start = self.__page*self.__perpage
        end = start + self.__perpage
        indexes = list(filter(lambda one: one < len(self.__obj), range(start, end)))
        this = [self.__obj[x] for x in indexes]
        
        return this