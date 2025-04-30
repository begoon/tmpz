import Testing

@Test func testA() {        
    #expect(1 + 1 == 2)
}

@Test("check", arguments: [1, 2, 3])
func check(_ n: Int)  {
  #expect(n == 1)
}
