from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client

# 自定义文件存储系统
class FastDFSStorage(Storage):
    def __init__(self, client_conf=None, server_ip = None):

        if client_conf is None:
            client_conf = settings.CLIENT_CONF
        self.client_conf = client_conf

        if server_ip is None:
            server_ip = settings.SERVER_IP
        self.server_ip = server_ip

    def _open(self):
        '''打开文件调用,主打存储,不会涉及到打开'''
        pass

    def _save(self, name, content):
        '''保存数据文件'''
        # name参数,要保存到fdfs中的文件的名字
        # content参数,要保存到fdfs的文件内容对象,可以直接调用read()方法,读取文件内容
        '''
        {'Group name': b'group1', 'Status': 'Upload successed.', 'Local file name': '', 'Remote file_id': b'group1/M00/00/00/Cv4H4lo1Bb6Aa8AEAAAABCd_gfM4135286', 'Storage IP': b'10.254.7.226', 'Uploaded size': '4B'}
        '''
        # 创建fdfs客户端
        client = Fdfs_client(self.client_conf)
        # 读取文件内容二进制数据
        flie_data = content.read()
        print(flie_data)
        # 上传到fdfs
        try:
            ret = client.upload_by_buffer(flie_data)

        except Exception as e:
            print(e)
            raise e
        # 判断上传是否成功
        if ret.get('Status') == 'Upload successed.':
            # 上传成功，需要把file_id存储到数据库中
            file_id = ret.get('Remote file_id')
            # 直接return即可，因为将来需要通过站点发布内容，如果是从df_GoodsSKU进入的站点，默认保存到df_GoodsSKU
            return file_id.decode()
        else:
            # 上传失败:在封装工具类时，如果有可能出现的地方，交给框架的使用者解决，写框架的人只需要提示riase
            raise Exception('上传失败')

    def exists(self, name):
        # 由于Djnago不存储图片，所以永远返回Fasle，直接保存到FastFDS
        return False

    def url(self, name):
        """用于返回图片在服务器上完整的地址：server_ip+path"""
        return self.server_ip + name
