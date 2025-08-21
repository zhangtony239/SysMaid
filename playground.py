import sysmaid as maid

if __name__ == "__main__":
    Canva = maid.Setup('Canva.exe')
    
    @Canva.has_no_window
    def taskkill():
        print("Canva process has no window, terminating...")
        maid.kill(Canva)

    maid.start()