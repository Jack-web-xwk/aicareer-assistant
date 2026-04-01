# 多图片粘贴功能增强

## 修改内容

### 文件：`frontend/src/pages/TargetJobUrlPage.tsx`

**修改时间**: 2026-03-31

**功能**: 支持在"目标岗位"页面使用 Ctrl+V 同时粘贴多张截图

---

## 修改细节

### 原有逻辑（单张图片）

```typescript
// 旧代码：只能处理第一张图片，遇到图片后立即返回
for (let i = 0; i < items.length; i++) {
  const item = items[i]
  if (item.kind === 'file' && item.type.startsWith('image/')) {
    // ... 处理图片
    setFileList([{
      uid: `paste-${Date.now()}`,
      name: file.name,
      status: 'done',
      originFileObj: file as unknown as UploadFile['originFileObj'],
    }])
    message.success('已粘贴截图，可点击「识别截图并保存」')
    return  // ❌ 只处理一张就返回
  }
}
```

### 新逻辑（多张图片）

```typescript
// 新代码：遍历所有剪贴板项目，收集所有图片
const imageFiles: UploadFile[] = []

for (let i = 0; i < items.length; i++) {
  const item = items[i]
  if (item.kind === 'file' && item.type.startsWith('image/')) {
    const blob = item.getAsFile()
    if (!blob) continue
    e.preventDefault()
    const sub = blob.type.split('/')[1]?.replace('jpeg', 'jpg') || 'png'
    const file = new File([blob], `paste-${Date.now()}-${i}.${sub}`, {
      type: blob.type || 'image/png',
    })
    imageFiles.push({
      uid: `paste-${Date.now()}-${i}`,
      name: file.name,
      status: 'done',
      originFileObj: file as unknown as UploadFile['originFileObj'],
    })
  }
}

if (imageFiles.length > 0) {
  // ✅ 追加到现有文件列表，支持同时粘贴多张图片
  setFileList((prev) => [...prev, ...imageFiles])
  message.success(`已粘贴 ${imageFiles.length} 张截图，可点击「识别截图并保存」`)
}
```

---

## 关键改动

### 1. 文件命名唯一化
```typescript
// 旧：paste-${Date.now()}.${sub}
// 新：paste-${Date.now()}-${i}.${sub}
// 添加索引 i 防止同一次粘贴的多张图片重名
```

### 2. 文件列表追加而非替换
```typescript
// 旧：setFileList([{ ... }]) // 替换整个列表
// 新：setFileList((prev) => [...prev, ...imageFiles]) // 追加到现有列表
```

### 3. 消息提示优化
```typescript
// 旧：'已粘贴截图，可点击「识别截图并保存」'
// 新：`已粘贴 ${imageFiles.length} 张截图，可点击「识别截图并保存」`
// 显示具体粘贴的图片数量
```

---

## 使用场景

### 场景 1：单次粘贴单张图片
- 用户截取一张岗位详情页截图
- 按 Ctrl+V 粘贴
- 结果：上传列表中添加 1 张图片

### 场景 2：单次粘贴多张图片（新功能）
- 用户截取多张岗位详情页截图（例如不同岗位）
- 使用截图工具同时复制到剪贴板（某些工具支持）
- 或连续多次 Ctrl+V 粘贴
- 结果：上传列表中累加多张图片

### 场景 3：混合使用
- 先拖拽上传 2 张图片
- 再按 Ctrl+V 粘贴 1 张图片
- 结果：上传列表中共有 3 张图片

---

## 技术实现

### 剪贴板事件处理
```typescript
useEffect(() => {
  document.addEventListener('paste', onPasteClipboardImage)
  return () => document.removeEventListener('paste', onPasteClipboardImage)
}, [onPasteClipboardImage])
```

### 文件列表状态管理
```typescript
const [fileList, setFileList] = useState<UploadFile[]>([])
```

### 防重复上传
- 每张图片使用唯一 UID：`paste-${Date.now()}-${i}`
- 使用 `beforeUpload={() => false}` 阻止自动上传
- 手动调用 `handleScreenshotUpload()` 统一处理

---

## 测试验证

### 测试步骤
1. 打开"职位中心" → "目标岗位"
2. 截取 1-3 张岗位详情页截图并复制到剪贴板
3. 在页面任意位置按 Ctrl+V
4. 观察上传列表是否显示对应数量的图片
5. 点击"识别截图并保存"按钮
6. 验证后端是否正确处理所有图片

### 预期结果
- ✅ 单张粘贴：列表显示 1 张图片
- ✅ 多张粘贴：列表显示多张图片（累加）
- ✅ 消息提示：显示正确的图片数量
- ✅ 文件命名：每张图片 UID 唯一
- ✅ 上传成功：后端正确识别所有图片

---

## 兼容性说明

### 浏览器支持
- Chrome/Edge: ✅ 完全支持
- Firefox: ✅ 完全支持
- Safari: ✅ 部分支持（取决于剪贴板 API）

### 操作系统
- Windows: ✅ Ctrl+V
- macOS: ✅ ⌘+V
- Linux: ✅ Ctrl+V

---

## 注意事项

1. **剪贴板内容限制**
   - 只能识别图片文件（`item.type.startsWith('image/')`）
   - 文本、文件等其他内容会被忽略

2. **事件阻止**
   - 检测到图片时会调用 `e.preventDefault()` 阻止默认粘贴行为
   - 避免图片粘贴到其他输入框中

3. **加载状态**
   - 如果正在上传（`loading === true`），粘贴事件会被忽略
   - 防止并发上传导致混乱

4. **文件去重**
   - 当前实现不会主动去重
   - 如果用户重复粘贴相同图片，会添加多个副本
   - 用户可手动在上传列表中删除

---

## 与拖拽上传的对比

| 功能 | 拖拽上传 | Ctrl+V 粘贴 |
|------|---------|------------|
| 多文件支持 | ✅ 支持 | ✅ 支持（本次增强） |
| 文件选择器 | ❌ 不需要 | ❌ 不需要 |
| 截图工具集成 | ❌ 需要保存文件 | ✅ 直接粘贴 |
| 操作路径 | 拖拽 → 上传 | 复制 → 粘贴 → 上传 |
| 适用场景 | 已有图片文件 | 截图后立即上传 |

---

## 用户体验提升

### 优化前
- ❌ 只能单张粘贴
- ❌ 需要保存截图文件再拖拽
- ❌ 无法批量操作

### 优化后
- ✅ 支持多张粘贴（累加）
- ✅ 截图后直接 Ctrl+V
- ✅ 配合截图工具可批量操作
- ✅ 显示具体图片数量提示

---

## 相关文件

- **前端页面**: `frontend/src/pages/TargetJobUrlPage.tsx`
- **上传组件**: Ant Design Upload Component
- **类型定义**: `frontend/src/types/index.ts`
- **API 服务**: `frontend/src/services/api.ts`

---

## 总结

本次修改通过**收集所有剪贴板图片项目**并**追加到文件列表**，实现了 Ctrl+V 同时粘贴多张截图的功能，与拖拽上传功能保持一致的用户体验。

**核心改动**: 3 处
1. 文件命名添加索引保证唯一性
2. 文件列表从"替换"改为"追加"
3. 消息提示显示图片数量

**代码行数**: +16 行，-11 行

**影响范围**: 仅"目标岗位"页面的截图上传功能
