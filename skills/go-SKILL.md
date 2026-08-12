---
description: "Go 编码技能 — error 处理、nil 陷阱、接口设计、并发安全、模块边界。修改 .go 前必读。"
name: "Go 编码技能"
argument-hint: "[修改的 .go 文件/模块] [--context 新增功能 | 修复缺陷 | 重构]"
---

# Go 编码技能

> 适用于 Go 1.22+。修改 .go 前必读。

## 1. Error 处理（最高频错误）

Go 没有 exception，error 是普通值。**每个 error 必须检查**。

```go
// ❌ 错误：忽略 error
result, _ := json.Marshal(data)

// ✅ 正确：检查 error
result, err := json.Marshal(data)
if err != nil {
    return fmt.Errorf("marshal failed: %w", err)
}

// ❌ 错误：直接返回 error，丢失上下文
return err

// ✅ 正确：包装 error（fmt.Errorf + %w 保持 error chain）
return fmt.Errorf("compute mean: %w", err)
```

### 哨兵契约（L2 哨兵：NaN 表示无效）

> 术语统一：SSOT 定义为「哨兵契约」（见 [rules/sentinel-contract.md](../rules/sentinel-contract.md)，
> L1-L5 各语言落地映射）。

```go
// 数值计算中 0 是有效值（均值=0、计数=0）
// 用 NaN 表示"无效"，不用 error 表示"计算结果为 0"

// ✅ 哨兵契约模式
func Mean(values []float64) float64 {
    if len(values) == 0 {
        return math.NaN() // 哨兵：空输入 → NaN
    }
    sum, count := 0.0, 0
    for _, v := range values {
        if math.IsNaN(v) || math.IsInf(v, 0) {
            continue // 静默过滤无效值
        }
        sum += v
        count++ // 分母是有效值计数，不是 len(values)
    }
    if count == 0 {
        return math.NaN() // 全部无效 → NaN
    }
    return sum / float64(count)
}

// ❌ 错误：用 error 表示"结果为 0"
// func Mean(values []float64) (float64, error) {
//     result := sum / float64(len(values))
//     if result == 0 { return 0, errors.New("zero result") } // 0 是有效值！
// }
```

### errors.Is / errors.As

```go
// ✅ 使用 errors.Is 比较 sentinel error
if errors.Is(err, sql.ErrNoRows) {
    // 记录不存在
}

// ✅ 使用 errors.As 提取类型化 error
var pathErr *fs.PathError
if errors.As(err, &pathErr) {
    log.Printf("path: %s, op: %s", pathErr.Path, pathErr.Op)
}
```

## 2. nil 陷阱

```go
// ❌ 错误：接口持有 nil 指针时 != nil
func main() {
    var p *MyStruct = nil
    var i interface{} = p
    if i != nil { // true! 接口非 nil（有类型信息），但底层指针是 nil
        // 会进入这里 → panic on method call
    }
}

// ✅ 正确：显式 nil 检查或避免将 nil 指针赋给接口
var i interface{} = nil
if i != nil { // false
    // 不进入
}

// ❌ 错误：map 未初始化就写入
var m map[string]int
m["a"] = 1 // panic: assignment to entry in nil map

// ✅ 正确：make 初始化
m := make(map[string]int)
m["a"] = 1
```

## 3. Slice 陷阱

```go
// ❌ 危险：切片引用底层数组，修改影响原数据
a := []int{1, 2, 3, 4, 5}
b := a[1:3] // [2, 3]
b[0] = 99  // a 变为 [1, 99, 3, 4, 5]！

// ✅ 安全：需要修改时 copy
b := make([]int, len(a[1:3]))
copy(b, a[1:3])

// ✅ append 可能创建新底层数组（cap 超出时）
b := append([]int{}, a[1:3]...) // 独立副本

// ❌ 错误：for range 中修改不影响原 slice
for i, v := range s {
    v *= 2 // 只修改局部变量 v，不影响 s[i]
}

// ✅ 正确：通过索引修改
for i := range s {
    s[i] *= 2
}
```

## 4. 并发安全

```go
// ❌ 错误：多 goroutine 写 map 不加锁
m := make(map[string]int)
for i := 0; i < 10; i++ {
    go func() { m["key"] = i }() // panic: concurrent map writes
}

// ✅ 正确：sync.Mutex 或 channel
var mu sync.Mutex
m := make(map[string]int)
for i := 0; i < 10; i++ {
    go func() {
        mu.Lock()
        defer mu.Unlock()
        m["key"] = i
    }()
}

// ✅ 更好：sync.Map（高并发读多写少）
var m sync.Map
m.Store("key", 1)
v, ok := m.Load("key")
```

### goroutine 生命周期

```go
// ❌ 错误：goroutine 泄漏（无退出条件）
func server() {
    for {
        conn, _ := listener.Accept()
        go func() {
            for { /* 永不退出 */ }
        }()
    }
}

// ✅ 正确：context 控制
func server(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        default:
            conn, _ := listener.Accept()
            go handle(ctx, conn)
        }
    }
}
```

## 5. 接口设计

```go
// ✅ 小接口（Go 惯例：接口定义在消费侧）
type Reader interface {
    Read(p []byte) (n int, err error)
}

// ❌ 避免：大接口（违反 ISP）
type Service interface {
    Method1() error
    Method2() error
    Method3() error
    // ... 20 个方法
}

// ✅ 接口组合
type ReadWriter interface {
    Reader
    Writer
}
```

## 6. 测试约定

```go
// table-driven test（Go 惯例）
func TestMean(t *testing.T) {
    tests := []struct {
        name   string
        input  []float64
        want   float64
    }{
        {"normal", []float64{1, 2, 3}, 2.0},
        {"all zeros", []float64{0, 0, 0}, 0.0},   // 0 是有效值
        {"negative", []float64{-1, -2, -3}, -2.0},
        {"empty", []float64{}, math.NaN()},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Mean(tt.input)
            if math.IsNaN(tt.want) {
                if !math.IsNaN(got) {
                    t.Errorf("Mean() = %v, want NaN", got)
                }
            } else if got != tt.want {
                t.Errorf("Mean() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

## 7. 提交前必检

- [ ] `go vet ./...` 零警告
- [ ] `go test ./...` 全绿
- [ ] 无 `_` 忽略 error（有则附注释说明原因）
- [ ] 无 goroutine 泄漏（每个 go 语句有退出路径）
- [ ] 无并发写 map 无锁
- [ ] 新增 Public 接口已同步 api-reference.md
- [ ] error 已包装上下文（`fmt.Errorf("context: %w", err)`）
- [ ] 无 interface{} 滥用（有则考虑泛型或具体类型）
