# Mnist in Docker
欢迎！Mnist in Docker是由来自MIT LIGO LAB的Dr.Fan指导，本人独立完成的大数据实习项目，本仓库目前包含以下内容：

- 项目打包成的Docker镜像文件Mnist_fianl.tar
- 项目报告
- 项目演示视频（Demo_Video.mp4）
- 项目源码（包括各历史版本的测试代码、模型训练代码、图像转换代码）
- MNIST训练模型（.ckpt文件）

### 当前版本（V3.0）功能描述
用户在宿主机上通过curl指令，将含有数字0~9的图片（.png）Post至本地服务器，服务器返回上传文件名、数字识别结果以及文件上传时间，并将其保存在Cassandra数据库中。目前可以实现的特性有：

:white_check_mark: 项目本地运行
:white_check_mark: 项目部署在Docker容器中运行
:white_check_mark: 利用docker volume将主机上存有训练模型的目录挂载到容器内的指定目录，从而能在容器内直接载入宿主机上的训练模型。



## 使用指南
### 运行前的准备
请确保您的主机装有`Docker`环境及`curl`工具，可在命令行中键入`docker --version` `curl --version`以验证是否成功安装。

将本项目clone到本地，打开命令行进入镜像文件所在目录，并键入以下命令：
```
$docker load -i Mnist_final.tar
```
载入成功后，通过`docker images`指令，您将看到名为`final_v3:v3`的镜像。

### 启动Docker容器
在命令行中键入以下指令：
```
$docker run -v [主机上模型文件夹路径]:/app/Big_Data/models -p 4000:80 -it final_v3:v3
```
:warning:务必将`[主机上...]`替换为存储ckpt文件的文件夹路径，由于容器中没有模型文件，如无法正确挂载，服务将无法正常运行。

键入以下命令以进入容器：（容器ID可通过`docker ps`查看）
```
$docker exec -it [容器ID] bash
```

启动服务器：
```
$python /app/final_mnist.py
```

### 上传图片
在命令行中键入：
```
curl -F "file=@[要上传的.png文件路径]" localhost:4000/upload
```
得到返回值：
```
Upload File Name: [filename]
Result: [result]
Upload Time: [time]
```

### 连接Cassandra数据库
通过cqlsh连接Cassandra数据库来查看文件名、结果及上传时间是否正确存储。

键入以下命令以进入容器：（容器ID可通过`docker ps`查看）
```
$docker exec -it [容器ID] bash
```
运行cqlsh:
```
$cd /usr/bin
$cqlsh localhost
```
查看Table是否被正确Insert，在cqlsh中依次输入以下指令：
```
use mnist_data;
Select * from mytable;
```



#### :arrow_forward:具体演示见视频文件 Demo_Video.mp4
