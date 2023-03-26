from goods.models import GoodsChannel

def get_categories():
    # 1,定义字典categories中
    categories = {}

    # 2,获取频道(一级分类)
    channels = GoodsChannel.objects.order_by("group_id", "sequence")

    # 3,遍历频道
    for channel in channels:
        # 3,1 获取频道中的组号
        group_id = channel.group_id

        # 3,2 判断组号是否在categories中
        if group_id not in categories:
            categories[group_id] = {"channels": [], "sub_cats": []}

        # 3,3 获取一级分类
        category1 = channel.category
        category1_dict = {
            "id": channel.id,
            "name": category1.name,
            "url": channel.url
        }

        # 3,4 添加一级分类到categories中
        categories[group_id]["channels"].append(category1_dict)

        # 3,5 获取二级分类
        cats2 = category1.subs.all()

        # 3,6 添加二级分类到categories中
        for cat2 in cats2:
            categories[group_id]["sub_cats"].append(cat2)

    # 4,返回分类数据
    return categories