import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
wsgi_app = "graduateCheck.wsgi:applicaton"
chdir=  "/Users/yeongroksong/Desktop/study/project/django/kuPhilGraduate/graduateCheck"
