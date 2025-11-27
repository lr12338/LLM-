
url：https://github.com/lr12338/LLM-.git
master：git push -u origin master

新增 / 修改文件后，推送更新：
bash
git add .
git commit -m "更新"
git push

拉取远程仓库的更新（如多人协作时）：
bash
git pull origin main

https://github.com/lr12338/LLM-.git




#### 一、准备工作
- 安装 Git：
  - macOS（Homebrew）：
  ```bash
  brew install git
  ```
  - Windows：访问 `https://git-scm.com/download/win` 安装 Git for Windows（含 Git Bash）
  - Linux（Debian/Ubuntu）：
  ```bash
  sudo apt update && sudo apt install -y git
  ```

- 配置用户名与邮箱（首次必做）：
  ```bash
  git config --global user.name "你的名字"
  git config --global user.email "你的邮箱@example.com"
  git config --global -l
  ```

- 生成 SSH 密钥（推荐免密推送/拉取）：
  ```bash
  ssh-keygen -t ed25519 -C "你的邮箱@example.com"
  # 生成：~/.ssh/id_ed25519 与 ~/.ssh/id_ed25519.pub
  cat ~/.ssh/id_ed25519.pub
  ```
  把 `.pub` 内容添加到 GitHub/Gitee 的 SSH Keys，测试：
  ```bash
  ssh -T git@github.com   # 或 git@gitee.com
  ```

---

#### 二、把新项目纳入 Git 管理
1) 在项目根目录初始化：
```bash
cd /path/to/your/project
git init
```
2) 创建 `.gitignore`（忽略不应入库的文件，如日志、缓存、虚拟环境、构建产物等）：
```bash
# Python 示例 .gitignore
__pycache__/
*.pyc
.venv/
.env
.DS_Store
build/
dist/
```
3) 首次提交：
```bash
git add .
git commit -m "chore: initialize project"
```
4) 关联远程仓库（以 GitHub 为例，Gitee 同理）：
```bash
# HTTPS（可能需输入账号/Token）
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
# SSH（推荐）
git remote add origin git@github.com:<你的用户名>/<仓库名>.git
```
5) 推送到远程主分支（main 或 master，按你的远程默认分支）：
```bash
git branch -M main
git push -u origin main
```

---

#### 三、克隆已有项目
```bash
# HTTPS
git clone https://github.com/<owner>/<repo>.git
# SSH（推荐）
git clone git@github.com:<owner>/<repo>.git
```
进入项目目录后，按项目说明安装依赖并运行。

---

#### 四、推荐的分支协作模型
- main：稳定可发布分支
- feat/xxx：功能开发分支
- fix/xxx：问题修复分支

示例流程：
```bash
# 基于最新 main 创建功能分支
git switch main
git pull --ff-only origin main
git switch -c feat/your-feature

# 开发并提交
git add .
git commit -m "feat: 实现 xxx 功能"

# 推送到远程
git push -u origin feat/your-feature
```
在平台发起 Pull Request/Merge Request，评审通过后合并回 main。

---

#### 五、常用命令速查
- 查看状态与差异：
```bash
git status
git diff
git diff --staged
```
- 提交与修改提交信息：
```bash
git add <文件或目录>
git commit -m "type: 简要说明"
# 修正上一条提交信息（未推送前）
git commit --amend -m "新的提交信息"
```
- 拉取更新：
```bash
git pull --ff-only
# 或
git pull --rebase
```
- 合并与变基：
```bash
# 合并分支（在目标分支上）
git switch main
git merge feat/your-feature

# 变基到最新 main（推送前做更安全）
git switch feat/your-feature
git fetch origin
git rebase origin/main
```
- 撤销与回退：
```bash
git restore <文件>
git restore --staged <文件>

git reset --soft HEAD~1
git reset --mixed HEAD~1
git reset --hard HEAD~1
```

---

#### 六、解决合并冲突（简要）
1) 冲突文件中会出现如下标记：
```text
<<<<<<< HEAD
你的修改
=======
对方的修改
>>>>>>> 分支名/提交
```
2) 手动编辑、保留正确内容并删除标记。
3) 标记解决后：
```bash
git add <冲突文件>
git commit
```

---

#### 七、提交信息与分支命名建议
- 提交类型：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore`
- 信息格式：`type(scope): message`
```text
feat(api): 新增船舶信息查询接口
fix(ui): 修复移动端导航遮挡
```
- 分支命名：`feat/xxx-描述`、`fix/bug-编号-描述`

---

#### 八、远程仓库管理
```bash
git remote -v
git remote set-url origin git@github.com:<owner>/<repo>.git
# 添加第二远程（例如 Gitee）
git remote add gitee git@gitee.com:<owner>/<repo>.git
git push origin main
git push gitee main
```

---

#### 九、常见问题（FAQ）
- 推送被拒绝（远程领先本地）：
```bash
git pull --rebase origin main
# 解决冲突后再推送
git push origin main
```
- 提交的作者信息写错（未推送）：
```bash
git commit --amend --author="姓名 <邮箱@example.com>"
```
- 新电脑推送失败：通常是未配置 SSH Key 或远程地址仍为 HTTPS，建议配置 SSH 并改为 SSH。

---

#### 十、进一步学习
- 官方文档：`https://git-scm.com/doc`
- Pro Git（中文）：`https://git-scm.com/book/zh/v2`
- GitHub 文档：`https://docs.github.com/`
- Gitee 帮助：`https://gitee.com/help`

---

如需将本仓库的子目录独立为新仓库，可了解 `git subtree` 等进阶用法。
