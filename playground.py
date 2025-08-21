import sysmaid as maid

if __name__ == "__main__":
    Canva = maid.SetWatchdog('Canva.exe')
    
    @Canva.is_exited
    def on_exit():
        maid.kill(Canva) # kill the process by its name