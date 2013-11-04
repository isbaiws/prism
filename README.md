### 这只是一个demo，没有任何错误处理，请善待他。
比如
> curl -X POST localhost:8008/email -d '{"subjecj": "ggfdsfdsa"}' -v

将在工作目录的recv子目录下，创建一个叫email的文件，内容是{"subjecj": "ggfdsfdsa"}
> curl -X GET localhost:8008/email -v

将recv目录下的email文件内容返回

***注意：***
1. 不要往根目录下写东西
2. content-length一定要设对
