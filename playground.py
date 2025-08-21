import sysmaid as maid

if __name__ == "__main__":

    Canva = maid.attend('Canva.exe')
    @Canva.has_no_window
    def _():
        maid.kill_process(Canva)

    CrossDeviceResume = maid.attend('CrossDeviceResume.exe')
    @CrossDeviceResume.has_no_window
    def _():
        maid.kill_process(CrossDeviceResume)

    GameViewer = maid.attend('GameViewer.exe')
    @GameViewer.is_exited
    def _():
        maid.stop_service('GameViewerService')

    maid.set_log_level('INFO')
    maid.start()