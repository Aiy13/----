main() {
    int x = 5;
    float y = 3.14;
    int z;
    
    z = x + y;  // 类型不匹配警告：int + float
    
    if (x) {  // 类型错误：if条件应为bool类型
        y = 10;
    }
    
    while (z > 0) {
        z = z - 1;
    }
    
    w = 5;  // 错误：变量w未声明
}