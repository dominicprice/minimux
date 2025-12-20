from minimux.buffer import Buffer


def test_buffer():
    buf = Buffer(20, 5, 4)

    buf.push("line 1\n")
    assert buf.screen.display == [
        "line 1              ",
        "                    ",
        "                    ",
        "                    ",
        "                    ",
    ]

    buf.push("this line is longer than the twenty character limit\n")
    assert buf.screen.display == [
        "line 1              ",
        "this line is longer ",
        "than the twenty char",
        "acter limit         ",
        "                    ",
    ]

    buf.push("this \033[0;32mis green\033[0m\n")
    assert buf.screen.display == [
        "this line is longer ",
        "than the twenty char",
        "acter limit         ",
        "this is green       ",
        "                    ",
    ]
