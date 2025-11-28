
新增 / 修改文件后，推送更新：
bash
git add .
git commit -m "更新"
git push
拉取远程仓库的更新（如多人协作时）：
bash
git pull origin master

https://github.com/lr12338/LLM-.git

### 重新配置更新
一、第一步：清理本地 Git 远程配置（核心，只清关联，不删文件）
# 1. 移除现有的 origin 远程仓库关联（清理核心）
git remote remove origin

# 2. 验证是否移除成功（执行后无任何输出，说明清理干净了）
git remote -v
二、第二步：重新初始化 Git 仓库（可选，彻底重置提交记录）
# 1. 先暂存所有本地文件（避免初始化后文件被标记为未跟踪）
git add .
# 2. 提交暂存的文件（生成一个全新的本地提交记录）
git commit -m "初始化 HifleetAIVideo 项目"
三、第三步：重新关联远程仓库 + 强制上传（避免冲突）
# （如果不想重置提交记录，跳过这两步，直接进入第三步）
# 1. 重新添加正确的远程仓库（和之前的地址一致，确保没写错）
git remote add origin https://github.com/lr12338/LLM-.git
# 2. 直接强制推送本地 master 分支到远程（覆盖远程分支，解决历史分歧）
git push -f origin master