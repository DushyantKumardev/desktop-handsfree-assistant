import * as Neutralino from '@neutralinojs/lib';

export const isNativeEnvironment = (): boolean => {
  return typeof window !== 'undefined' && (window as unknown as { NL_PORT?: number }).NL_PORT !== undefined;
};

let trayConfigured = false;

export const setupSystemTray = async (): Promise<void> => {
  if (!isNativeEnvironment() || trayConfigured) return;

  try {
    trayConfigured = true;
    await Neutralino.os.setTray({
      icon: '/resources/icons/trayIcon.png',
      menuItems: [
        { id: 'SHOW', text: 'Show Assistant' },
        { id: 'SEP', text: '-' },
        { id: 'QUIT', text: 'Quit Assistant' },
      ],
    });

    Neutralino.events.on('trayMenuItemClicked', async (evt: any) => {
      if (evt?.detail?.id === 'SHOW') {
        await Neutralino.window.show();
        await Neutralino.window.focus();
      } else if (evt?.detail?.id === 'QUIT') {
        await Neutralino.app.exit();
      }
    });

    console.log('[Desktop] System tray setup complete');
  } catch (err) {
    console.warn('[Desktop] Failed to setup system tray:', err);
  }
};

export const minimizeToTray = async (): Promise<void> => {
  if (isNativeEnvironment()) {
    try {
      await Neutralino.window.hide();
      console.log('[Desktop] Window hidden to tray');
    } catch (err) {
      console.warn('[Desktop] Failed to hide to tray:', err);
    }
  } else {
    console.log('[Desktop] Window hidden to tray (browser mock)');
  }
};

export const showWindow = async (): Promise<void> => {
  if (isNativeEnvironment()) {
    try {
      await Neutralino.window.show();
      await Neutralino.window.focus();
      console.log('[Desktop] Window shown and focused');
    } catch (err) {
      console.warn('[Desktop] Failed to show window:', err);
    }
  } else {
    console.log('[Desktop] Window shown (browser mock)');
  }
};

export const showNativeNotification = async (title: string, content: string): Promise<void> => {
  if (isNativeEnvironment()) {
    try {
      await Neutralino.os.showNotification(title, content, 'INFO');
      console.log(`[Desktop] Native notification shown: ${title} - ${content}`);
    } catch (err) {
      console.warn('[Desktop] Failed to show native notification:', err);
    }
  } else {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification(title, { body: content });
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then((permission) => {
          if (permission === 'granted') {
            new Notification(title, { body: content });
          }
        });
      }
    }
    console.log(`[Desktop] [Browser Notification] ${title}: ${content}`);
  }
};

export const registerBlurAutoHide = (onBlurCallback?: () => void): void => {
  const handleBlur = () => {
    minimizeToTray();
    if (onBlurCallback) onBlurCallback();
  };

  if (isNativeEnvironment()) {
    try {
      Neutralino.events.on('windowBlur', handleBlur);
    } catch (e) {
      console.warn(e);
    }
  }
  window.addEventListener('blur', handleBlur);
};

export const initDesktopRuntime = (onReady?: () => void): void => {
  if (isNativeEnvironment()) {
    try {
      Neutralino.init();
      console.log('[Desktop] Runtime initialized');
      Neutralino.events.on('ready', () => {
        console.log('[Desktop] Neutralino ready event received');
        setupSystemTray();
        if (onReady) onReady();
      });
      // In case ready event already fired
      setTimeout(() => {
        setupSystemTray();
        if (onReady) onReady();
      }, 100);
    } catch (err) {
      console.warn('[Desktop] Runtime init failed:', err);
    }
  }
};

export const makeElementDraggable = async (elementId: string): Promise<void> => {
  if (isNativeEnvironment()) {
    try {
      await Neutralino.window.setDraggableRegion(elementId);
      console.log(`[Desktop] Window draggable region registered on #${elementId}`);
    } catch (err) {
      console.warn('[Desktop] Failed to register draggable region:', err);
    }
  }
};

let isDragging = false;
let startScreenX = 0;
let startScreenY = 0;
let initialWindowX = 0;
let initialWindowY = 0;

export const handleWindowDrag = async (e: React.MouseEvent): Promise<void> => {
  if (e.button !== 0 || (e.target as HTMLElement).closest('button, input, textarea, a')) {
    return;
  }
  if (!isNativeEnvironment()) return;

  try {
    isDragging = true;
    startScreenX = e.screenX;
    startScreenY = e.screenY;

    const pos = await Neutralino.window.getPosition();
    initialWindowX = pos.x ?? 0;
    initialWindowY = pos.y ?? 0;

    const cleanup = () => {
      isDragging = false;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', cleanup);
      window.removeEventListener('pointerup', cleanup);
      window.removeEventListener('blur', cleanup);
    };

    const onMouseMove = async (moveEvent: MouseEvent) => {
      // If mouse button is no longer held down, immediately stop dragging
      if (!isDragging || moveEvent.buttons === 0) {
        cleanup();
        return;
      }
      const deltaX = moveEvent.screenX - startScreenX;
      const deltaY = moveEvent.screenY - startScreenY;
      await Neutralino.window.move(initialWindowX + deltaX, initialWindowY + deltaY);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', cleanup);
    window.addEventListener('pointerup', cleanup);
    window.addEventListener('blur', cleanup);
  } catch (err) {
    console.warn('[Desktop] Window drag error:', err);
  }
};

export const setWindowSize = async (width: number, height: number): Promise<void> => {
  if (isNativeEnvironment()) {
    try {
      // Read current state in parallel
      const [pos, size] = await Promise.all([
        Neutralino.window.getPosition(),
        Neutralino.window.getSize(),
      ]);
      const currentX = pos.x ?? 0;
      const currentY = pos.y ?? 0;
      const currentH = size.height ?? height;
      const deltaH = height - currentH;

      // Resize first, then shift Y so the bottom edge (pill) stays put
      await Neutralino.window.setSize({ width, height });
      if (deltaH !== 0) {
        await Neutralino.window.move(currentX, currentY - deltaH);
      }
    } catch (err) {
      console.warn('[Desktop] Failed to resize window:', err);
    }
  }
};

export const desktopWindow = {
  minimize: async (): Promise<void> => {
    if (isNativeEnvironment()) {
      await Neutralino.window.minimize();
    } else {
      console.log('[Desktop] Window minimize called');
    }
  },
  hide: async (): Promise<void> => {
    if (isNativeEnvironment()) {
      await Neutralino.window.hide();
    } else {
      console.log('[Desktop] Window hide called');
    }
  },
  show: async (): Promise<void> => {
    if (isNativeEnvironment()) {
      await Neutralino.window.show();
    } else {
      console.log('[Desktop] Window show called');
    }
  },
  close: async (): Promise<void> => {
    if (isNativeEnvironment()) {
      await Neutralino.app.exit();
    } else {
      window.close();
    }
  },
};

