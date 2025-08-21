import sysmaid as maid

if __name__ == "__main__":

    Canva = maid.attend('Canva.exe')
    @Canva.has_no_window
    def _():
        maid.kill_process('Canva.exe')

    WeMeetApp = maid.attend('WeMeetApp.exe')
    @WeMeetApp.has_no_window
    def _():
        maid.kill_process('WeMeetApp.exe')

    CrossDeviceResume = maid.attend('CrossDeviceResume.exe')
    @CrossDeviceResume.is_running
    def _():
        maid.kill_process('CrossDeviceResume.exe')

    GameViewer = maid.attend('GameViewer.exe')
    @GameViewer.is_exited
    def _():
        maid.stop_service('GameViewerService')

    maid.set_log_level('ERROR')
    maid.start()