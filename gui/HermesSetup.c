/*
 * HermesSetup.exe - Hermes Agent Windows GUI Launcher
 *
 * Compile (Linux/MinGW cross-compile):
 *   x86_64-w64-mingw32-gcc -o HermesSetup.exe HermesSetup.c \
 *     -mwindows -lcomctl32 -lwinhttp -lshell32 -lshlwapi \
 *     -DUNICODE -D_UNICODE -O2 -s
 *
 * Compile (Windows/MSVC):
 *   cl HermesSetup.c /Fe:HermesSetup.exe /link comctl32.lib winhttp.lib shell32.lib shlwapi.lib
 */

#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <commctrl.h>
#include <winhttp.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <wchar.h>
#include <stdio.h>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "winhttp.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")

/* ── Control IDs ────────────────────────────────────────────────── */
#define IDC_TAB              100

/* Tab 0: Hermes */
#define IDC_HERMES_STATUS    101
#define IDC_BTN_START_HERMES 102
#define IDC_BTN_STOP_HERMES  103
#define IDC_HERMES_LOG       104

/* Tab 1: Web UI */
#define IDC_WEBUI_STATUS     201
#define IDC_GATEWAY_STATUS   202
#define IDC_NODE_VERSION     203
#define IDC_WEBUI_URL        204
#define IDC_BTN_START_WEBUI  205
#define IDC_BTN_STOP_WEBUI   206
#define IDC_BTN_OPEN_BROWSER 207
#define IDC_WEBUI_LOG        208

/* Timer */
#define TIMER_REFRESH        1001
#define TIMER_INTERVAL_MS    3000

/* ── Globals ─────────────────────────────────────────────────────── */
static HINSTANCE g_hInst;
static wchar_t   g_installDir[MAX_PATH];   /* directory of this .exe */
static wchar_t   g_homeDir[MAX_PATH];      /* %USERPROFILE% */
static int       g_currentTab = 0;

/* Tab 0 controls */
static HWND g_hHermesStatus, g_hBtnStartHermes, g_hBtnStopHermes, g_hHermesLog;
/* Tab 1 controls */
static HWND g_hWebuiStatus, g_hGatewayStatus, g_hNodeVersion, g_hWebuiUrl;
static HWND g_hBtnStartWebui, g_hBtnStopWebui, g_hBtnOpenBrowser, g_hWebuiLog;
/* Tab control */
static HWND g_hTab;

/* ── Helper: append text to a multiline EDIT ─────────────────────── */
static void AppendLog(HWND hEdit, const wchar_t* msg) {
    int len = GetWindowTextLengthW(hEdit);
    SendMessageW(hEdit, EM_SETSEL, len, len);
    SendMessageW(hEdit, EM_REPLACESEL, FALSE, (LPARAM)msg);
    SendMessageW(hEdit, EM_REPLACESEL, FALSE, (LPARAM)L"\r\n");
    SendMessageW(hEdit, EM_SCROLL, SB_BOTTOM, 0);
}

/* ── HTTP health check via WinHTTP (no extra deps) ───────────────── */
static BOOL CheckHttpHealth(const wchar_t* host, INTERNET_PORT port, const wchar_t* path) {
    BOOL ok = FALSE;
    HINTERNET hSession = WinHttpOpen(L"HermesSetup/1.0",
        WINHTTP_ACCESS_TYPE_NO_PROXY, NULL, NULL, 0);
    if (!hSession) return FALSE;

    HINTERNET hConnect = WinHttpConnect(hSession, host, port, 0);
    if (!hConnect) { WinHttpCloseHandle(hSession); return FALSE; }

    HINTERNET hReq = WinHttpOpenRequest(hConnect, L"GET", path,
        NULL, NULL, NULL, 0);
    if (!hReq) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return FALSE;
    }

    /* 2-second timeout */
    DWORD timeout = 2000;
    WinHttpSetOption(hReq, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hReq, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    if (WinHttpSendRequest(hReq, NULL, 0, NULL, 0, 0, 0) &&
        WinHttpReceiveResponse(hReq, NULL)) {
        DWORD status = 0, sz = sizeof(status);
        WinHttpQueryHeaders(hReq,
            WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
            NULL, &status, &sz, NULL);
        ok = (status == 200);
    }

    WinHttpCloseHandle(hReq);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    return ok;
}

/* ── Get Node.js version string ──────────────────────────────────── */
static void GetNodeVersion(wchar_t* outBuf, DWORD bufSize) {
    wchar_t nodeExe[MAX_PATH];
    _snwprintf(nodeExe, MAX_PATH, L"%snode_embedded\\node.exe", g_installDir);

    if (!PathFileExistsW(nodeExe)) {
        wcsncpy(outBuf, L"未安装", bufSize);
        return;
    }

    wchar_t cmdLine[MAX_PATH + 32];
    _snwprintf(cmdLine, MAX_PATH + 32, L"\"%s\" --version", nodeExe);

    SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
    HANDLE hRead, hWrite;
    if (!CreatePipe(&hRead, &hWrite, &sa, 0)) {
        wcsncpy(outBuf, L"未知", bufSize);
        return;
    }

    STARTUPINFOW si = { sizeof(si) };
    si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.hStdOutput = hWrite;
    si.hStdError  = hWrite;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi = {0};
    if (CreateProcessW(NULL, cmdLine, NULL, NULL, TRUE,
            CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        CloseHandle(hWrite);
        char buf[64] = {0};
        DWORD read = 0;
        ReadFile(hRead, buf, sizeof(buf) - 1, &read, NULL);
        WaitForSingleObject(pi.hProcess, 3000);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        /* strip trailing \r\n */
        for (int i = (int)read - 1; i >= 0; i--) {
            if (buf[i] == '\r' || buf[i] == '\n') buf[i] = 0; else break;
        }
        MultiByteToWideChar(CP_UTF8, 0, buf, -1, outBuf, (int)bufSize);
    } else {
        CloseHandle(hWrite);
        wcsncpy(outBuf, L"未知", bufSize);
    }
    CloseHandle(hRead);
}

/* ── Launch a .bat hidden + async ───────────────────────────────── */
static BOOL LaunchBat(const wchar_t* batPath) {
    if (!PathFileExistsW(batPath)) return FALSE;

    wchar_t cmdLine[MAX_PATH + 64];
    _snwprintf(cmdLine, MAX_PATH + 64, L"cmd.exe /c \"%s\"", batPath);

    STARTUPINFOW si = { sizeof(si) };
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi = {0};
    BOOL ok = CreateProcessW(NULL, cmdLine, NULL, NULL, FALSE,
        CREATE_NEW_CONSOLE, NULL, g_installDir, &si, &pi);
    if (ok) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }
    return ok;
}

/* ── Kill process by reading PID file ───────────────────────────── */
static void KillByPidFile(const wchar_t* pidFile) {
    HANDLE hFile = CreateFileW(pidFile, GENERIC_READ, FILE_SHARE_READ,
        NULL, OPEN_EXISTING, 0, NULL);
    if (hFile == INVALID_HANDLE_VALUE) return;

    char buf[32] = {0};
    DWORD read;
    ReadFile(hFile, buf, sizeof(buf) - 1, &read, NULL);
    CloseHandle(hFile);

    DWORD pid = (DWORD)atoi(buf);
    if (pid == 0) return;

    HANDLE hProc = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
    if (hProc) {
        TerminateProcess(hProc, 0);
        CloseHandle(hProc);
    }
    DeleteFileW(pidFile);
}

/* ── Open browser with token ────────────────────────────────────── */
static void OpenBrowserWithToken(void) {
    wchar_t tokenFile[MAX_PATH];
    _snwprintf(tokenFile, MAX_PATH, L"%s\\.hermes-web-ui\\.token", g_homeDir);

    wchar_t token[128] = {0};
    HANDLE hFile = CreateFileW(tokenFile, GENERIC_READ, FILE_SHARE_READ,
        NULL, OPEN_EXISTING, 0, NULL);
    if (hFile != INVALID_HANDLE_VALUE) {
        char raw[128] = {0};
        DWORD read;
        ReadFile(hFile, raw, sizeof(raw) - 1, &read, NULL);
        CloseHandle(hFile);
        for (int i = (int)read - 1; i >= 0; i--) {
            if (raw[i] == '\r' || raw[i] == '\n') raw[i] = 0; else break;
        }
        MultiByteToWideChar(CP_UTF8, 0, raw, -1, token, 128);
    }

    wchar_t url[512];
    if (wcslen(token) > 0)
        _snwprintf(url, 512, L"http://localhost:8648/#/?token=%s", token);
    else
        wcscpy(url, L"http://localhost:8648");

    ShellExecuteW(NULL, L"open", url, NULL, NULL, SW_SHOWNORMAL);
}

/* ── Refresh Tab 1 (Web UI) status ─────────────────────────────── */
static void RefreshWebuiStatus(void) {
    BOOL gwOk = CheckHttpHealth(L"127.0.0.1", 8642, L"/health");
    BOOL uiOk = CheckHttpHealth(L"127.0.0.1", 8648, L"/health");

    SetWindowTextW(g_hGatewayStatus,
        gwOk ? L"● 运行中 (port 8642)" : L"○ 已停止");
    SetWindowTextW(g_hWebuiStatus,
        uiOk ? L"● 运行中" : L"○ 已停止");
    SetWindowTextW(g_hWebuiUrl,
        uiOk ? L"http://localhost:8648" : L"—");

    wchar_t nodeVer[64];
    GetNodeVersion(nodeVer, 64);
    SetWindowTextW(g_hNodeVersion, nodeVer);

    EnableWindow(g_hBtnStartWebui,  !uiOk);
    EnableWindow(g_hBtnStopWebui,    uiOk);
    EnableWindow(g_hBtnOpenBrowser,  uiOk);
}

/* ── Refresh Tab 0 (Hermes) status ─────────────────────────────── */
static void RefreshHermesStatus(void) {
    BOOL gwOk = CheckHttpHealth(L"127.0.0.1", 8642, L"/health");
    SetWindowTextW(g_hHermesStatus,
        gwOk ? L"● Hermes gateway 运行中 (port 8642)" : L"○ 未运行");
    EnableWindow(g_hBtnStartHermes, !gwOk);
    EnableWindow(g_hBtnStopHermes,   gwOk);
}

/* ── Show/hide controls for the active tab ──────────────────────── */
static void ShowTab(int tab) {
    /* Tab 0 controls */
    int show0 = (tab == 0) ? SW_SHOW : SW_HIDE;
    ShowWindow(g_hHermesStatus,    show0);
    ShowWindow(g_hBtnStartHermes,  show0);
    ShowWindow(g_hBtnStopHermes,   show0);
    ShowWindow(g_hHermesLog,       show0);

    /* Tab 1 controls */
    int show1 = (tab == 1) ? SW_SHOW : SW_HIDE;
    ShowWindow(g_hWebuiStatus,     show1);
    ShowWindow(g_hGatewayStatus,   show1);
    ShowWindow(g_hNodeVersion,     show1);
    ShowWindow(g_hWebuiUrl,        show1);
    ShowWindow(g_hBtnStartWebui,   show1);
    ShowWindow(g_hBtnStopWebui,    show1);
    ShowWindow(g_hBtnOpenBrowser,  show1);
    ShowWindow(g_hWebuiLog,        show1);
}

/* ── Create all child controls ──────────────────────────────────── */
static void CreateControls(HWND hWnd) {
    HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    int W = 620, H = 440;  /* inner area below tab */
    int px = 10, py = 40;  /* padding inside tab area */

    /* ── Tab 0: Hermes ── */
    g_hHermesStatus = CreateWindowExW(0, L"STATIC", L"○ 检测中...",
        WS_CHILD | SS_LEFT,
        px, py, W - px*2, 20, hWnd, (HMENU)IDC_HERMES_STATUS, g_hInst, NULL);

    g_hBtnStartHermes = CreateWindowExW(0, L"BUTTON", L"启动 Hermes",
        WS_CHILD | BS_PUSHBUTTON,
        px, py + 30, 120, 28, hWnd, (HMENU)IDC_BTN_START_HERMES, g_hInst, NULL);

    g_hBtnStopHermes = CreateWindowExW(0, L"BUTTON", L"停止 Hermes",
        WS_CHILD | BS_PUSHBUTTON,
        px + 130, py + 30, 120, 28, hWnd, (HMENU)IDC_BTN_STOP_HERMES, g_hInst, NULL);

    g_hHermesLog = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | ES_MULTILINE | ES_READONLY | ES_AUTOVSCROLL |
        WS_VSCROLL | WS_HSCROLL,
        px, py + 70, W - px*2, H - py - 80,
        hWnd, (HMENU)IDC_HERMES_LOG, g_hInst, NULL);

    /* ── Tab 1: Web UI ── */
    /* Status info box */
    CreateWindowExW(0, L"STATIC", L"Gateway:",
        WS_CHILD | SS_LEFT,
        px, py, 70, 18, hWnd, NULL, g_hInst, NULL);
    g_hGatewayStatus = CreateWindowExW(0, L"STATIC", L"○ 检测中...",
        WS_CHILD | SS_LEFT,
        px + 75, py, W - px*2 - 75, 18,
        hWnd, (HMENU)IDC_GATEWAY_STATUS, g_hInst, NULL);

    CreateWindowExW(0, L"STATIC", L"Web UI:",
        WS_CHILD | SS_LEFT,
        px, py + 22, 70, 18, hWnd, NULL, g_hInst, NULL);
    g_hWebuiStatus = CreateWindowExW(0, L"STATIC", L"○ 检测中...",
        WS_CHILD | SS_LEFT,
        px + 75, py + 22, W - px*2 - 75, 18,
        hWnd, (HMENU)IDC_WEBUI_STATUS, g_hInst, NULL);

    CreateWindowExW(0, L"STATIC", L"地址:",
        WS_CHILD | SS_LEFT,
        px, py + 44, 70, 18, hWnd, NULL, g_hInst, NULL);
    g_hWebuiUrl = CreateWindowExW(0, L"STATIC", L"—",
        WS_CHILD | SS_LEFT,
        px + 75, py + 44, W - px*2 - 75, 18,
        hWnd, (HMENU)IDC_WEBUI_URL, g_hInst, NULL);

    CreateWindowExW(0, L"STATIC", L"Node.js:",
        WS_CHILD | SS_LEFT,
        px, py + 66, 70, 18, hWnd, NULL, g_hInst, NULL);
    g_hNodeVersion = CreateWindowExW(0, L"STATIC", L"检测中...",
        WS_CHILD | SS_LEFT,
        px + 75, py + 66, 200, 18,
        hWnd, (HMENU)IDC_NODE_VERSION, g_hInst, NULL);

    /* Buttons */
    g_hBtnStartWebui = CreateWindowExW(0, L"BUTTON", L"启动 Web UI",
        WS_CHILD | BS_PUSHBUTTON,
        px, py + 100, 120, 28,
        hWnd, (HMENU)IDC_BTN_START_WEBUI, g_hInst, NULL);

    g_hBtnStopWebui = CreateWindowExW(0, L"BUTTON", L"停止 Web UI",
        WS_CHILD | BS_PUSHBUTTON,
        px + 130, py + 100, 120, 28,
        hWnd, (HMENU)IDC_BTN_STOP_WEBUI, g_hInst, NULL);

    g_hBtnOpenBrowser = CreateWindowExW(0, L"BUTTON", L"打开浏览器",
        WS_CHILD | BS_PUSHBUTTON,
        px + 260, py + 100, 120, 28,
        hWnd, (HMENU)IDC_BTN_OPEN_BROWSER, g_hInst, NULL);

    /* Log area */
    g_hWebuiLog = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | ES_MULTILINE | ES_READONLY | ES_AUTOVSCROLL |
        WS_VSCROLL | WS_HSCROLL,
        px, py + 140, W - px*2, H - py - 150,
        hWnd, (HMENU)IDC_WEBUI_LOG, g_hInst, NULL);

    /* Apply default font to all controls */
    HWND controls[] = {
        g_hHermesStatus, g_hBtnStartHermes, g_hBtnStopHermes, g_hHermesLog,
        g_hGatewayStatus, g_hWebuiStatus, g_hWebuiUrl, g_hNodeVersion,
        g_hBtnStartWebui, g_hBtnStopWebui, g_hBtnOpenBrowser, g_hWebuiLog
    };
    for (int i = 0; i < (int)(sizeof(controls)/sizeof(controls[0])); i++) {
        if (controls[i])
            SendMessageW(controls[i], WM_SETFONT, (WPARAM)hFont, TRUE);
    }
}

/* ── Window procedure ───────────────────────────────────────────── */
static LRESULT CALLBACK WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {

    case WM_CREATE: {
        /* Initialize common controls (Tab Control needs this) */
        INITCOMMONCONTROLSEX icc = { sizeof(icc), ICC_TAB_CLASSES };
        InitCommonControlsEx(&icc);

        /* Tab control */
        g_hTab = CreateWindowExW(0, WC_TABCONTROLW, NULL,
            WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | TCS_FIXEDWIDTH,
            0, 0, 640, 500, hWnd, (HMENU)IDC_TAB, g_hInst, NULL);

        HFONT hFont = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        SendMessageW(g_hTab, WM_SETFONT, (WPARAM)hFont, TRUE);
        TabCtrl_SetItemSize(g_hTab, 120, 24);

        TCITEMW tie = { TCIF_TEXT };
        tie.pszText = L"  Hermes";
        TabCtrl_InsertItem(g_hTab, 0, &tie);
        tie.pszText = L"  Web UI";
        TabCtrl_InsertItem(g_hTab, 1, &tie);

        CreateControls(hWnd);
        ShowTab(0);

        /* Initial status refresh + timer */
        RefreshHermesStatus();
        SetTimer(hWnd, TIMER_REFRESH, TIMER_INTERVAL_MS, NULL);

        AppendLog(g_hHermesLog, L"Hermes Agent 已就绪。");
        AppendLog(g_hHermesLog, L"点击 [启动 Hermes] 开始运行。");
        break;
    }

    case WM_TIMER:
        if (wParam == TIMER_REFRESH) {
            if (g_currentTab == 0) RefreshHermesStatus();
            else                    RefreshWebuiStatus();
        }
        break;

    case WM_NOTIFY: {
        NMHDR* pnm = (NMHDR*)lParam;
        if (pnm->idFrom == IDC_TAB && pnm->code == TCN_SELCHANGE) {
            g_currentTab = TabCtrl_GetCurSel(g_hTab);
            ShowTab(g_currentTab);
            if (g_currentTab == 0) RefreshHermesStatus();
            else                    RefreshWebuiStatus();
        }
        break;
    }

    case WM_COMMAND: {
        WORD id = LOWORD(wParam);
        wchar_t batPath[MAX_PATH];
        wchar_t pidFile[MAX_PATH];

        switch (id) {

        /* ── Tab 0 buttons ── */
        case IDC_BTN_START_HERMES:
            _snwprintf(batPath, MAX_PATH, L"%sstart_hermes_gateway.bat", g_installDir);
            if (LaunchBat(batPath)) {
                AppendLog(g_hHermesLog, L"[INFO] 正在启动 Hermes gateway...");
            } else {
                AppendLog(g_hHermesLog, L"[ERROR] 找不到 start_hermes_gateway.bat");
            }
            break;

        case IDC_BTN_STOP_HERMES:
            _snwprintf(pidFile, MAX_PATH, L"%s\\.hermes\\gateway.pid", g_homeDir);
            KillByPidFile(pidFile);
            AppendLog(g_hHermesLog, L"[INFO] Gateway 已停止。");
            RefreshHermesStatus();
            break;

        /* ── Tab 1 buttons ── */
        case IDC_BTN_START_WEBUI: {
            wchar_t nodeExe[MAX_PATH];
            _snwprintf(nodeExe, MAX_PATH, L"%snode_embedded\\node.exe", g_installDir);
            if (!PathFileExistsW(nodeExe)) {
                AppendLog(g_hWebuiLog,
                    L"[ERROR] Node.js 未安装。请运行 install.bat full");
                MessageBoxW(hWnd,
                    L"Web UI 需要完整版安装。\n\n"
                    L"请在安装目录下运行：\ninstall.bat full",
                    L"需要完整版", MB_OK | MB_ICONINFORMATION);
                break;
            }
            _snwprintf(batPath, MAX_PATH, L"%sstart_webui.bat", g_installDir);
            if (LaunchBat(batPath)) {
                AppendLog(g_hWebuiLog, L"[INFO] 正在启动 Web UI (约30秒)...");
            } else {
                AppendLog(g_hWebuiLog, L"[ERROR] 找不到 start_webui.bat");
            }
            break;
        }

        case IDC_BTN_STOP_WEBUI:
            _snwprintf(pidFile, MAX_PATH, L"%s\\.hermes-web-ui\\server.pid", g_homeDir);
            KillByPidFile(pidFile);
            AppendLog(g_hWebuiLog, L"[INFO] Web UI 已停止。");
            RefreshWebuiStatus();
            break;

        case IDC_BTN_OPEN_BROWSER:
            OpenBrowserWithToken();
            AppendLog(g_hWebuiLog, L"[INFO] 已在浏览器中打开。");
            break;
        }
        break;
    }

    case WM_SIZE: {
        int W = LOWORD(lParam), H = HIWORD(lParam);
        if (g_hTab) MoveWindow(g_hTab, 0, 0, W, H, TRUE);
        /* Resize log areas to fill available space */
        int logW = W - 20, logH = H - 240;
        if (logH < 80) logH = 80;
        if (g_hHermesLog) MoveWindow(g_hHermesLog, 10, 110, logW, logH, TRUE);
        if (g_hWebuiLog)  MoveWindow(g_hWebuiLog,  10, 180, logW, logH, TRUE);
        break;
    }

    case WM_DESTROY:
        KillTimer(hWnd, TIMER_REFRESH);
        PostQuitMessage(0);
        break;

    default:
        return DefWindowProcW(hWnd, msg, wParam, lParam);
    }
    return 0;
}

/* ── WinMain ────────────────────────────────────────────────────── */
int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE hPrev, LPWSTR lpCmd, int nShow) {
    (void)hPrev; (void)lpCmd;
    g_hInst = hInst;

    /* Resolve install dir (directory of this .exe) */
    GetModuleFileNameW(NULL, g_installDir, MAX_PATH);
    PathRemoveFileSpecW(g_installDir);
    wcsncat(g_installDir, L"\\", MAX_PATH - wcslen(g_installDir) - 1);

    /* Resolve home dir */
    ExpandEnvironmentStringsW(L"%USERPROFILE%", g_homeDir, MAX_PATH);

    /* Register window class */
    WNDCLASSEXW wc = { sizeof(wc) };
    wc.style         = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc   = WndProc;
    wc.hInstance     = hInst;
    wc.hCursor       = LoadCursorW(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.lpszClassName = L"HermesSetupClass";
    wc.hIcon         = LoadIconW(NULL, IDI_APPLICATION);
    wc.hIconSm       = LoadIconW(NULL, IDI_APPLICATION);
    RegisterClassExW(&wc);

    /* Create main window */
    HWND hWnd = CreateWindowExW(
        WS_EX_APPWINDOW,
        L"HermesSetupClass",
        L"Hermes Agent",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        660, 540,
        NULL, NULL, hInst, NULL);

    if (!hWnd) return 1;

    ShowWindow(hWnd, nShow);
    UpdateWindow(hWnd);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}
