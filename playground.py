import sysmaid as maid

if __name__ == "__main__":

    Canva = maid.attend('Canva.exe')
    
    @Canva.has_no_window
    def taskkill():
        maid.kill(Canva)

    WeMeet = maid.attend('WeMeet.exe')

    maid.set_log_level('INFO')
    maid.start()