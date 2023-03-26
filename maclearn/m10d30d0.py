import happybase

def scanQuery():
    # 创建和Hbase服务器连接，获取connection对象
    connection = happybase.Connection('192.168.19.137')
    # 通过connection传入表名
    table = connection.table('user')
    filter = "ColumnPrefixFilter('username')"

    result = table.scan(row_start='rowkey_16', filter=filter)

    for row_key, row_data in result:
        print(row_key, row_data)



    connection.close()

def getQuery():
    connection = happybase.Connection('192.168.19.137')
    table = connection.table('user')
    result = table.row('rowkey_16', columns=['base_info:username'])




if __name__ == '__main__':

    # connection = happybase.Connection('192.168.19.137')
    # # connection.create_table('user2', {'cf1':dict()})
    # connection.delete_table('user2', disable=True)
    #
    #
    #
    # print(connection.tables())
    scanQuery()




















    # connection.close()

