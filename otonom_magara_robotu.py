# -*- coding: utf-8 -*-
"""
Necmettin Erbakan Üniversitesi - Bilgisayar Mühendisliği Bölümü
Robotik Dersi Dönem Ödevi Projesi
Konu: Otonom Mağara Keşif ve Haritalama Robotu Simülasyonu
Öğrenci: Ömer Faruk Kahraman
Öğrenci No: 21370031058
"""

import pygame
import sys
import random
import math

# --- RENKLER (Sleek & Cyberpunk Tasarım) ---
COLOR_BG = (13, 17, 23)           # Ana arka plan (koyu gri/mavi)
COLOR_PANEL_BG = (21, 27, 38)     # Bilgi paneli arka planı
COLOR_TEXT = (226, 232, 240)       # Ana yazı rengi
COLOR_TEXT_MUTED = (148, 163, 184) # Yardımcı yazı rengi
COLOR_ACCENT = (99, 102, 241)     # Başlıklar ve vurgular (indigo)

# Harita Durum Renkleri
COLOR_UNEXPLORED = (15, 23, 42)    # Keşfedilmemiş alan (çok koyu lacivert)
COLOR_FREE_SPACE = (241, 245, 249) # Keşfedilmiş boş alan (kırık beyaz)
COLOR_MAPPED_WALL = (239, 68, 68)  # Robotun tespit ettiği duvar (neon kırmızı)
COLOR_ACTUAL_WALL = (51, 65, 85)   # Gerçek mağara duvarı referansı (isteğe bağlı gösterim için - koyu gri)

# Robot ve Sensör Renkleri
COLOR_ROBOT = (34, 197, 94)       # Robot gövdesi (neon yeşil)
COLOR_ROBOT_DIR = (220, 38, 38)    # Robot yön göstergesi (kırmızı)
COLOR_LASER = (249, 115, 22)       # LiDAR Lazer ışınları (turuncu)
COLOR_PATH = (59, 130, 246)        # Robotun izlediği yol (neon mavi)

# Durum Renk Haritası
STATE_COLORS = {
    "KESIF": (34, 197, 94),       # Yeşil
    "DONUS": (234, 179, 8),       # Sarı
    "GERI CEKILME": (239, 68, 68),# Kırmızı
    "MANUEL": (59, 130, 246)      # Mavi
}

# --- YARDIMCI FONKSİYONLAR ---

def generate_cave(width, height):
    """
    Hücresel Otomat (Cellular Automata) kullanarak organik mağara yapısı üretir.
    """
    # İlk olarak rastgele doldur (yaklaşık %43 duvar oranı)
    grid = [[1 if random.random() < 0.43 else 0 for _ in range(width)] for _ in range(height)]
    
    # Sınırları duvar yap
    for x in range(width):
        grid[0][x] = 1
        grid[height-1][x] = 1
    for y in range(height):
        grid[y][0] = 1
        grid[y][width-1] = 1
        
    # 5 iterasyon hücresel otomat kurallarını uygula
    for _ in range(5):
        new_grid = [row[:] for row in grid]
        for y in range(1, height-1):
            for x in range(1, width-1):
                # 3x3 komşuluktaki duvarları say
                walls = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        walls += grid[y+dy][x+dx]
                
                # Kural: Etrafta 4'ten fazla duvar varsa hücre duvara dönüşür
                if walls > 4:
                    new_grid[y][x] = 1
                else:
                    new_grid[y][x] = 0
        grid = new_grid
        
    return grid

def clean_cave(grid):
    """
    Mağaradaki izole odacıkları temizler, sadece en büyük boş alanı bırakır.
    Böylece robotun kapalı küçük alanlarda sıkışması önlenir.
    """
    height = len(grid)
    width = len(grid[0])
    visited = [[False for _ in range(width)] for _ in range(height)]
    components = []
    
    # Flood-fill ile tüm boş odaları (bağlantılı bileşenleri) bul
    for y in range(1, height-1):
        for x in range(1, width-1):
            if grid[y][x] == 0 and not visited[y][x]:
                queue = [(x, y)]
                visited[y][x] = True
                comp = []
                while queue:
                    cx, cy = queue.pop(0)
                    comp.append((cx, cy))
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            if grid[ny][nx] == 0 and not visited[ny][nx]:
                                visited[ny][nx] = True
                                queue.append((nx, ny))
                components.append(comp)
                
    if not components:
        return grid, (width // 2, height // 2)
        
    # En büyük boş alanı bul
    largest_comp = max(components, key=len)
    
    # En büyük boş alan dışındaki tüm boş alanları duvarla kapla
    clean_grid = [[1 for _ in range(width)] for _ in range(height)]
    for x, y in largest_comp:
        clean_grid[y][x] = 0
        
    # Sınırları koru
    for x in range(width):
        clean_grid[0][x] = 1
        clean_grid[height-1][x] = 1
    for y in range(height):
        clean_grid[y][0] = 1
        clean_grid[y][width-1] = 1
        
    # Başlangıç pozisyonu olarak en büyük odanın rastgele bir hücresini seç
    start_pos = largest_comp[len(largest_comp) // 2]
    return clean_grid, start_pos

def bresenham_line(x0, y0, x1, y1):
    """
    Bresenham Çizgi Algoritması. 
    İki nokta arasındaki ızgara hücrelerinin listesini döner (SLAM haritalama için).
    """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points

# --- ROBOT SINIFI ---

class CaveRobot:
    def __init__(self, start_x, start_y, cell_size):
        self.cell_size = cell_size
        # Robotun piksel cinsinden konumu (hücre merkezinde başlatılır)
        self.x = (start_x * cell_size) + (cell_size / 2)
        self.y = (start_y * cell_size) + (cell_size / 2)
        
        self.angle = 0.0              # Robotun yönü (Radyan)
        self.radius = 12.0            # Robot yarıçapı
        self.speed = 0.0              # Mevcut hız
        self.max_speed = 2.0          # Maksimum ileri hız
        self.angular_speed = 0.06     # Dönüş hızı (Radyan/kare)
        
        # LiDAR Sensör Parametreleri
        self.sensor_range = 180.0     # Maksimum tarama mesafesi (piksel)
        self.num_rays = 36            # Lazer ışını sayısı (360 derece tarama)
        self.lidar_data = []          # [(mesafe, hit_x, hit_y, duvar_mi), ...]
        
        # Durum Bilgileri
        self.state = "KESIF"          # KESIF, DONUS, GERI CEKILME, MANUAL
        self.battery = 100.0          # Pil seviyesi (%)
        self.path_history = []        # Gidilen yolun geçmiş koordinatları
        self.stuck_counter = 0        # Sıkışma kontrol sayacı
        self.last_pos = (self.x, self.y)
        
    def get_grid_pos(self):
        """Mevcut piksel konumunu harita hücre koordinatına çevirir."""
        return int(self.x // self.cell_size), int(self.y // self.cell_size)
        
    def update_lidar(self, grid):
        """
        Her yöne ışın göndererek mağara duvarlarına olan mesafeyi ölçer.
        """
        self.lidar_data = []
        grid_h = len(grid)
        grid_w = len(grid[0])
        
        for i in range(self.num_rays):
            # 360 dereceye yayılan ışın açısı
            ray_angle = self.angle + (i * (2 * math.pi / self.num_rays))
            
            cos_a = math.cos(ray_angle)
            sin_a = math.sin(ray_angle)
            
            # Adım adım ışın izleme (Raymarching)
            step = 3.0
            dist = 0.0
            hit = False
            hx, hy = self.x, self.y
            
            while dist < self.sensor_range:
                hx = self.x + dist * cos_a
                hy = self.y + dist * sin_a
                
                gx = int(hx // self.cell_size)
                gy = int(hy // self.cell_size)
                
                # Harita sınırları dışına çıkıldıysa veya duvara çarptıysa dur
                if 0 <= gx < grid_w and 0 <= gy < grid_h:
                    if grid[gy][gx] == 1:
                        hit = True
                        break
                else:
                    hit = True
                    break
                dist += step
                
            self.lidar_data.append((dist, hx, hy, hit))

    def update_map(self, mapped_grid):
        """
        LiDAR verilerini kullanarak robotun kendi haritasını (SLAM Grid) günceller.
        """
        grid_h = len(mapped_grid)
        grid_w = len(mapped_grid[0])
        rx, ry = self.get_grid_pos()
        
        for dist, hx, hy, hit in self.lidar_data:
            hx_grid = int(hx // self.cell_size)
            hy_grid = int(hy // self.cell_size)
            
            # Harita sınırlarında kal
            hx_grid = max(0, min(grid_w - 1, hx_grid))
            hy_grid = max(0, min(grid_h - 1, hy_grid))
            
            # Bresenham ile robot konumu ile ışının çarptığı nokta arasındaki hattı çiz
            ray_cells = bresenham_line(rx, ry, hx_grid, hy_grid)
            
            # Hat üzerindeki tüm hücreleri "boş alan (0)" olarak işaretle (engelsiz görüş hattı)
            for cx, cy in ray_cells[:-1]:
                if 0 <= cx < grid_w and 0 <= cy < grid_h:
                    # Daha önce duvar olarak haritalanmış olsa bile, robot şu an orayı boş görüyorsa düzeltir
                    mapped_grid[cy][cx] = 0
            
            # Lazer bir duvara çarptıysa, en uçtaki hücreyi "duvar (1)" olarak haritalandır
            if hit:
                cx, cy = ray_cells[-1]
                if 0 <= cx < grid_w and 0 <= cy < grid_h:
                    mapped_grid[cy][cx] = 1

    def move_manual(self, keys, grid):
        """Kullanıcı klavye kontrolleri ile robotu hareket ettirir."""
        self.state = "MANUAL"
        self.speed = 0.0
        
        # İleri - Geri hareket
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.speed = self.max_speed
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.speed = -self.max_speed / 2.0
            
        # Dönüş hareketi
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.angle -= self.angular_speed
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.angle += self.angular_speed
            
        self._apply_movement(grid)

    def move_autonomous(self, grid, mapped_grid):
        """
        Otonom Engel Sakınma, Duvar Takibi ve Keşfedilmemiş Alanlara (Frontier) yönelme algoritması.
        """
        self.update_lidar(grid)
        
        # Robotun etrafındaki sensör bölgelerini analiz et (36 ışın için)
        # Ön bölge: -30 derece ile +30 derece arası (Ray 0, 1, 2, 3 ve 33, 34, 35)
        front_rays_idx = [0, 1, 2, 3, 4, 31, 32, 33, 34, 35]
        left_rays_idx = [5, 6, 7, 8, 9, 10, 11, 12, 13]
        right_rays_idx = [23, 24, 25, 26, 27, 28, 29, 30]
        
        front_dists = [self.lidar_data[idx][0] for idx in front_rays_idx]
        left_dists = [self.lidar_data[idx][0] for idx in left_rays_idx]
        right_dists = [self.lidar_data[idx][0] for idx in right_rays_idx]
        
        min_front = min(front_dists)
        avg_left = sum(left_dists) / len(left_dists)
        avg_right = sum(right_dists) / len(right_dists)
        
        # Sıkışma Analizi
        dx = self.x - self.last_pos[0]
        dy = self.y - self.last_pos[1]
        dist_moved = math.sqrt(dx*dx + dy*dy)
        self.last_pos = (self.x, self.y)
        
        if dist_moved < 0.2:
            self.stuck_counter += 1
        else:
            self.stuck_counter = max(0, self.stuck_counter - 1)
            
        # Sıkışma eşiği aşılırsa Geri Çekilme durumuna geç
        if self.stuck_counter > 50:
            self.state = "GERI CEKILME"
            self.stuck_counter = 0
            
        # --- DURUM MAKİNESİ (STATE MACHINE) ---
        
        if self.state == "GERI CEKILME":
            # Geriye doğru hareket et ve yönü hafifçe değiştir
            self.speed = -self.max_speed / 2.0
            self.angle += self.angular_speed * 1.5
            # Ön taraf tamamen açılana kadar geri git
            if min_front > 80.0:
                self.state = "KESIF"
                
        elif self.state == "DONUS":
            # Engelin olmadığı yöne doğru yerinde dön
            self.speed = 0.0
            if avg_left > avg_right:
                self.angle -= self.angular_speed
            else:
                self.angle += self.angular_speed
                
            # Önümüzdeki yol temizlendiyse keşfe geri dön
            if min_front > 70.0:
                self.state = "KESIF"
                
        else:  # KESIF DURUMU
            self.state = "KESIF"
            
            # Karşımızda yakın bir engel var mı?
            if min_front < 50.0:
                self.state = "DONUS"
            else:
                # İleri git
                self.speed = self.max_speed
                
                # --- YÖNLENDİRME (STEERING) ALGORİTMASI ---
                # Robotun rotasını keşfedilmemiş alanlara doğru yönlendirelim
                steering_angle = self._get_unexplored_frontier_steering(mapped_grid)
                self.angle += steering_angle
                
                # Hafif duvar hizalama (Duvarı ortalama)
                if min(left_dists) < 35.0:
                    self.angle += 0.02 # Sağa hafif kır
                elif min(right_dists) < 35.0:
                    self.angle -= 0.02 # Sola hafif kır

        self._apply_movement(grid)

    def _get_unexplored_frontier_steering(self, mapped_grid):
        """
        Lazer ışınlarının gittiği açık doğrultulardaki 'keşfedilmemiş' hücre 
        oranlarını hesaplar ve robotu en yüksek potansiyele sahip yöne yönlendirir.
        """
        grid_h = len(mapped_grid)
        grid_w = len(mapped_grid[0])
        
        # Test edilecek 3 ana yön: Düz (self.angle), Hafif Sol, Hafif Sağ
        test_angles = {
            -0.6: 0, # Sol yön
             0.0: 0, # Düz yön
             0.6: 0  # Sağ yön
        }
        
        for offset in test_angles.keys():
            check_angle = self.angle + offset
            cos_a = math.cos(check_angle)
            sin_a = math.sin(check_angle)
            
            # Bu doğrultuda 100 piksellik bir hattı tara ve keşfedilmemiş hücreleri say
            unexplored_count = 0
            for d in range(20, 100, 10):
                tx = self.x + d * cos_a
                ty = self.y + d * sin_a
                gx = int(tx // self.cell_size)
                gy = int(ty // self.cell_size)
                
                if 0 <= gx < grid_w and 0 <= gy < grid_h:
                    if mapped_grid[gy][gx] == 0.5: # 0.5 = Keşfedilmemiş (Unexplored)
                        unexplored_count += 1
                        
            test_angles[offset] = unexplored_count
            
        # En çok keşfedilmemiş hücreye sahip yönü seç
        best_offset = max(test_angles, key=test_angles.get)
        
        # Eğer tüm yönler eşitse veya keşfedilmemiş alan yoksa dönme (0.0 döner)
        if test_angles[best_offset] == 0:
            return 0.0
            
        # Seçilen yöne doğru hafif dönüş açısı uygula
        return best_offset * 0.05

    def _apply_movement(self, grid):
        """Robotun fiziksel konumunu günceller ve duvar çarpışma kontrolü yapar."""
        grid_h = len(grid)
        grid_w = len(grid[0])
        
        # Hedef koordinatlar
        next_x = self.x + self.speed * math.cos(self.angle)
        next_y = self.y + self.speed * math.sin(self.angle)
        
        # Çarpışma algılama (Robotun gövde sınırları ile duvar kontrolü)
        can_move_x = True
        can_move_y = True
        
        # Robotun etrafında 8 dairesel test noktası ile çarpışma testi yapalım
        for angle_offset in range(0, 360, 45):
            rad_offset = math.radians(angle_offset)
            
            # X ekseninde test
            test_x = next_x + self.radius * math.cos(rad_offset)
            test_y = self.y + self.radius * math.sin(rad_offset)
            gx = int(test_x // self.cell_size)
            gy = int(test_y // self.cell_size)
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                if grid[gy][gx] == 1:
                    can_move_x = False
            else:
                can_move_x = False
                
            # Y ekseninde test
            test_x = self.x + self.radius * math.cos(rad_offset)
            test_y = next_y + self.radius * math.sin(rad_offset)
            gx = int(test_x // self.cell_size)
            gy = int(test_y // self.cell_size)
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                if grid[gy][gx] == 1:
                    can_move_y = False
            else:
                can_move_y = False
                
        # Konum güncelleme (Kayan engel davranışı: X veya Y ekseninde ayrı ayrı hareket edebilir)
        if can_move_x:
            self.x = next_x
        if can_move_y:
            self.y = next_y
            
        # Duvarın içine sıkışmayı önleyici aktif itme (Nudge Recovery)
        # Eğer robot hareket edemiyorsa ve duvara çok yakınsa zıt yöne ittirilir
        if not can_move_x or not can_move_y:
            self.stuck_counter += 1
            if self.stuck_counter > 25 and self.lidar_data:
                # En yakın duvar yönünü bul
                min_ray_idx = min(range(self.num_rays), key=lambda idx: self.lidar_data[idx][0])
                min_dist, _, _, hit = self.lidar_data[min_ray_idx]
                if hit and min_dist < self.radius + 8:
                    push_angle = self.angle + (min_ray_idx * (2 * math.pi / self.num_rays)) + math.pi
                    self.x += 2.0 * math.cos(push_angle)
                    self.y += 2.0 * math.sin(push_angle)
                    self.stuck_counter = 0 # Sıfırla
        else:
            self.stuck_counter = max(0, self.stuck_counter - 1)
            
        # Hareket halindeyken bataryayı tüket
        if self.speed != 0:
            self.battery = max(0.0, self.battery - 0.002)
            
        # Gidilen yolun geçmişini güncelle (Her 5 karede bir yeni konum ekle)
        if len(self.path_history) == 0 or math.dist((self.x, self.y), self.path_history[-1]) > 5:
            self.path_history.append((self.x, self.y))
            if len(self.path_history) > 300: # Belleği yormamak için maksimum 300 nokta tut
                self.path_history.pop(0)

# --- ANA SİMÜLASYON YÖNETİCİSİ ---

class SimulationApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("NEÜ Robotik - Otonom Mağara Robotu Simülasyonu (21370031058)")
        
        # Ekran Boyutları: Sol panel simülasyon (800x800), Sağ panel bilgi ekranı (400x800)
        self.sim_width = 800
        self.sim_height = 800
        self.panel_width = 400
        self.screen_width = self.sim_width + self.panel_width
        self.screen_height = 800
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_body = pygame.font.SysFont("Arial", 14)
        self.font_header = pygame.font.SysFont("Arial", 20, bold=True)
        
        # Harita Yapılandırması (80x80 hücreli harita)
        self.grid_size = 80
        self.cell_size = self.sim_width // self.grid_size # 800 / 80 = 10 piksel/hücre
        
        # Simülasyon Durumları
        self.show_actual_cave = True    # Gerçek mağara sınırlarını kırmızı çizgi olarak göster/gizle
        self.is_paused = False          # Simülasyonu duraklatma durumu
        self.manual_override = False    # Manuel kontrol modu
        
        self.reset_simulation()
        
    def reset_simulation(self):
        """Haritayı yeniden üretir ve robotu sıfırlar."""
        # 1. Mağara Oluştur
        raw_cave = generate_cave(self.grid_size, self.grid_size)
        # 2. Temizle (Bileşen analizi ile tek oda garantisi)
        self.cave_grid, start_pos = clean_cave(raw_cave)
        
        # 3. Robotu ata
        self.robot = CaveRobot(start_pos[0], start_pos[1], self.cell_size)
        
        # 4. Robotun Boş Haritasını oluştur (0.5 = Keşfedilmemiş)
        # Haritanın dış sınırlarını otomatik 1 (Duvar) olarak başlatabiliriz
        self.mapped_grid = [[0.5 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for x in range(self.grid_size):
            self.mapped_grid[0][x] = 1.0
            self.mapped_grid[self.grid_size-1][x] = 1.0
        for y in range(self.grid_size):
            self.mapped_grid[y][0] = 1.0
            self.mapped_grid[y][self.grid_size-1] = 1.0
            
        # Mağara içerisindeki toplam keşfedilebilir hücre sayısını hesapla
        self.total_explorable_cells = 0
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.cave_grid[y][x] == 0:
                    self.total_explorable_cells += 1
                    
        self.explored_percentage = 0.0

    def calculate_explored_percentage(self):
        """Robotun ne kadarlık boş mağara hücresini başarıyla keşfettiğini hesaplar."""
        discovered_empty = 0
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Gerçekte boş olan ve robotun da boş (0) olarak keşfettiği hücreler
                if self.cave_grid[y][x] == 0 and self.mapped_grid[y][x] == 0:
                    discovered_empty += 1
                    
        if self.total_explorable_cells > 0:
            self.explored_percentage = (discovered_empty / self.total_explorable_cells) * 100.0
        else:
            self.explored_percentage = 0.0

    def draw_simulation(self):
        """Sol taraftaki robotik simülasyon alanını çizer."""
        # Keşfedilmemiş alan rengiyle temizle
        pygame.draw.rect(self.screen, COLOR_UNEXPLORED, (0, 0, self.sim_width, self.sim_height))
        
        # Keşfedilmiş Haritayı Hücre Hücre Çiz
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                cell_val = self.mapped_grid[y][x]
                if cell_val == 0:   # Keşfedilmiş Boş Alan
                    rect = (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, COLOR_FREE_SPACE, rect)
                elif cell_val == 1: # Robotun tespit ettiği duvar
                    rect = (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, COLOR_MAPPED_WALL, rect)
                    
        # Robotun İlerleme Yol İzini Çiz (Mavi çizgi)
        if len(self.robot.path_history) > 1:
            pygame.draw.lines(self.screen, COLOR_PATH, False, self.robot.path_history, 2)
            
        # Lazer Işınlarını (LiDAR) Çiz
        if self.robot.battery > 0:
            for dist, hx, hy, hit in self.robot.lidar_data:
                # Yarı saydam lazer efektini taklit etmek için küçük bir daire veya hat çizebiliriz
                pygame.draw.line(self.screen, COLOR_LASER, (self.robot.x, self.robot.y), (hx, hy), 1)
                if hit:
                    # Çarpma noktasına küçük bir kırmızı lazer noktası çiz
                    pygame.draw.circle(self.screen, COLOR_MAPPED_WALL, (int(hx), int(hy)), 2)
                    
        # Referans Gerçek Mağara Sınırlarını İnce Çizgi Olarak Çiz (İstenirse)
        if self.show_actual_cave:
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    if self.cave_grid[y][x] == 1:
                        # Duvarların etrafına çizgi çiz
                        rect = (x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                        pygame.draw.rect(self.screen, COLOR_ACTUAL_WALL, rect, 1)

        # Robot Gövdesini Çiz
        pygame.draw.circle(self.screen, COLOR_ROBOT, (int(self.robot.x), int(self.robot.y)), int(self.robot.radius))
        # Yön Çizgisi
        dir_x = self.robot.x + self.robot.radius * math.cos(self.robot.angle)
        dir_y = self.robot.y + self.robot.radius * math.sin(self.robot.angle)
        pygame.draw.line(self.screen, COLOR_ROBOT_DIR, (self.robot.x, self.robot.y), (dir_x, dir_y), 3)

    def draw_panel(self):
        """Sağ taraftaki veri gösterge ve kontrol panelini çizer."""
        panel_rect = (self.sim_width, 0, self.panel_width, self.screen_height)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, COLOR_ACCENT, (self.sim_width, 0), (self.sim_width, self.screen_height), 2)
        
        y_offset = 25
        
        # 1. Başlıklar
        header_text = self.font_header.render("NECMETTİN ERBAKAN ÜNİ.", True, COLOR_TEXT)
        self.screen.blit(header_text, (self.sim_width + 25, y_offset))
        y_offset += 25
        
        sub_header = self.font_title.render("Bilgisayar Mühendisliği Bölümü", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub_header, (self.sim_width + 25, y_offset))
        y_offset += 35
        
        # Proje İsmi
        proj_text = self.font_title.render("OTONOM MAĞARA ROBOTU SİM.", True, COLOR_ACCENT)
        self.screen.blit(proj_text, (self.sim_width + 25, y_offset))
        y_offset += 25
        
        student_text = self.font_body.render("Ömer Faruk Kahraman - 21370031058", True, COLOR_TEXT)
        self.screen.blit(student_text, (self.sim_width + 25, y_offset))
        
        # Ayırıcı Hat
        y_offset += 30
        pygame.draw.line(self.screen, COLOR_ACTUAL_WALL, (self.sim_width + 20, y_offset), (self.screen_width - 20, y_offset), 1)
        y_offset += 20
        
        # 2. Sistem Durum Verileri
        data_title = self.font_title.render("SİSTEM GÖSTERGE PANELİ", True, COLOR_ACCENT)
        self.screen.blit(data_title, (self.sim_width + 25, y_offset))
        y_offset += 30
        
        # Aktif Durum
        state_label = self.font_body.render("Robot Durumu: ", True, COLOR_TEXT_MUTED)
        self.screen.blit(state_label, (self.sim_width + 25, y_offset))
        
        curr_state = self.robot.state
        if self.manual_override:
            curr_state = "MANUEL"
            
        state_val = self.font_title.render(curr_state, True, STATE_COLORS.get(curr_state, COLOR_TEXT))
        self.screen.blit(state_val, (self.sim_width + 150, y_offset))
        y_offset += 25
        
        # Keşif Yüzdesi
        exp_label = self.font_body.render("Harita Keşif Oranı: ", True, COLOR_TEXT_MUTED)
        self.screen.blit(exp_label, (self.sim_width + 25, y_offset))
        exp_val = self.font_title.render(f"{self.explored_percentage:.2f} %", True, COLOR_ROBOT)
        self.screen.blit(exp_val, (self.sim_width + 150, y_offset))
        
        # Küçük Keşif Barı
        y_offset += 20
        bar_x = self.sim_width + 25
        bar_w = 350
        pygame.draw.rect(self.screen, COLOR_UNEXPLORED, (bar_x, y_offset, bar_w, 8))
        pygame.draw.rect(self.screen, COLOR_ROBOT, (bar_x, y_offset, int(bar_w * (self.explored_percentage / 100.0)), 8))
        y_offset += 20
        
        # Batarya Durumu
        bat_label = self.font_body.render("Batarya Seviyesi: ", True, COLOR_TEXT_MUTED)
        self.screen.blit(bat_label, (self.sim_width + 25, y_offset))
        
        bat_color = COLOR_ROBOT if self.robot.battery > 50 else ((234, 179, 8) if self.robot.battery > 20 else COLOR_MAPPED_WALL)
        bat_val = self.font_title.render(f"{self.robot.battery:.1f} %", True, bat_color)
        self.screen.blit(bat_val, (self.sim_width + 150, y_offset))
        y_offset += 25
        
        # Koordinat Bilgileri
        coord_label = self.font_body.render("Robot Konumu (X, Y): ", True, COLOR_TEXT_MUTED)
        self.screen.blit(coord_label, (self.sim_width + 25, y_offset))
        gx, gy = self.robot.get_grid_pos()
        coord_val = self.font_body.render(f"Hücre: ({gx}, {gy})  Piksel: ({int(self.robot.x)}, {int(self.robot.y)})", True, COLOR_TEXT)
        self.screen.blit(coord_val, (self.sim_width + 150, y_offset))
        y_offset += 25
        
        # Açısal Bilgi
        angle_label = self.font_body.render("Robot Yön Açısı: ", True, COLOR_TEXT_MUTED)
        self.screen.blit(angle_label, (self.sim_width + 25, y_offset))
        angle_val = self.font_body.render(f"{math.degrees(self.robot.angle) % 360:.1f}° (Radyan: {self.robot.angle:.2f})", True, COLOR_TEXT)
        self.screen.blit(angle_val, (self.sim_width + 150, y_offset))
        y_offset += 25
        
        # LiDAR Işın Verileri
        lidar_label = self.font_body.render("LiDAR Sensör Menzili: ", True, COLOR_TEXT_MUTED)
        self.screen.blit(lidar_label, (self.sim_width + 25, y_offset))
        lidar_val = self.font_body.render(f"36 Işın (360°) / {int(self.robot.sensor_range)}m", True, COLOR_TEXT)
        self.screen.blit(lidar_val, (self.sim_width + 150, y_offset))
        
        # Ayırıcı Hat
        y_offset += 35
        pygame.draw.line(self.screen, COLOR_ACTUAL_WALL, (self.sim_width + 20, y_offset), (self.screen_width - 20, y_offset), 1)
        y_offset += 20
        
        # 3. Kontroller ve Tuş Kılavuzu
        ctrl_title = self.font_title.render("SİMÜLASYON KONTROL PANELİ", True, COLOR_ACCENT)
        self.screen.blit(ctrl_title, (self.sim_width + 25, y_offset))
        y_offset += 30
        
        controls = [
            ("[SPACE]", "Simülasyonu Duraklat / Devam Et"),
            ("[M]", "Otonom / Manuel Kontrol Modu"),
            ("[V]", "Gerçek Mağara Sınırlarını Göster / Gizle"),
            ("[R]", "Haritayı Yeniden Üret ve Robotu Sıfırla"),
            ("[C]", "Robot Bataryasını Doldur (%100)"),
            ("[YÖN / WASD]", "Manuel Modda Robotu Sürme")
        ]
        
        for key, desc in controls:
            key_text = self.font_title.render(key, True, COLOR_TEXT)
            self.screen.blit(key_text, (self.sim_width + 25, y_offset))
            desc_text = self.font_body.render(desc, True, COLOR_TEXT_MUTED)
            self.screen.blit(desc_text, (self.sim_width + 150, y_offset))
            y_offset += 22
            
        # 4. Duraklatma Bilgisi
        if self.is_paused:
            y_offset += 20
            paused_text = self.font_header.render("SİMÜLASYON DURAKLATILDI", True, COLOR_MAPPED_WALL)
            self.screen.blit(paused_text, (self.sim_width + 60, y_offset))

    def run(self):
        """Simülasyon döngüsünü başlatır."""
        running = True
        while running:
            # FPS'i 60'a sabitle
            self.clock.tick(60)
            
            # --- OLAY KONTROLLERİ ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_m:
                        self.manual_override = not self.manual_override
                        if not self.manual_override:
                            self.robot.state = "KESIF"
                    elif event.key == pygame.K_v:
                        self.show_actual_cave = not self.show_actual_cave
                    elif event.key == pygame.K_r:
                        self.reset_simulation()
                    elif event.key == pygame.K_c:
                        self.robot.battery = 100.0
            
            # --- FİZİK VE GÜNCELLEME DÖNGÜSÜ ---
            if not self.is_paused:
                keys = pygame.key.get_pressed()
                
                # Sadece pil varsa robot hareket edebilir
                if self.robot.battery > 0:
                    if self.manual_override:
                        self.robot.move_manual(keys, self.cave_grid)
                        self.robot.update_lidar(self.cave_grid)
                    else:
                        self.robot.move_autonomous(self.cave_grid, self.mapped_grid)
                else:
                    self.robot.speed = 0.0
                    
                # Robotun harita verilerini SLAM ızgarasına işle
                self.robot.update_map(self.mapped_grid)
                
                # Keşif oranını güncelle
                self.calculate_explored_percentage()
                
            # --- EKRAN ÇİZİM DÖNGÜSÜ ---
            self.draw_simulation()
            self.draw_panel()
            
            # Ekranı tazele
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = SimulationApp()
    app.run()
