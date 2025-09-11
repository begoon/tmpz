// https://www.youtube.com/watch?v=oVHarxAoQrY

const std = @import("std");

const Animal = struct {
    vtable: *const VTable,

    const VTable = struct {
        speak: *const fn (*const Animal) void,
    };

    pub fn speak(self: *const Animal) void {
        self.vtable.speak(self);
    }
};

const Dog = struct {
    interface: Animal,
    name: []const u8,

    fn speak_(interface: *const Animal) void {
        const self: *const Dog = @fieldParentPtr("interface", interface);
        std.debug.print("woof! I'm {s}\n", .{self.name});
    }

    const vtable = Animal.VTable{ .speak = speak_ };

    pub fn init(name: []const u8) Dog {
        return .{ .interface = .{ .vtable = &vtable }, .name = name };
    }
};

const Cat = struct {
    interface: Animal,
    name: []const u8,

    fn speak_(interface: *const Animal) void {
        const self: *const Cat = @fieldParentPtr("interface", interface);
        std.debug.print("meow~ I'm {s}\n", .{self.name});
    }

    const vtable = Animal.VTable{ .speak = speak_ };

    pub fn init(name: []const u8) Cat {
        return .{ .interface = .{ .vtable = &vtable }, .name = name };
    }
};

pub fn main() void {
    var dog = Dog.init("Rex");
    var cat = Cat.init("Misty");

    const zoo = [_]*const Animal{ &dog.interface, &cat.interface };
    for (zoo) |a| a.speak();
}
