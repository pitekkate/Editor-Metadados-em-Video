#pyinstaller --onefile seuscript.py

import tkinter as tk
from tkinter import filedialog, simpledialog, scrolledtext, ttk,Tk, Label, Entry, Button, messagebox, RADIOBUTTON
from pytube import YouTube
from moviepy.editor import VideoFileClip, vfx
import subprocess
import os
import random
import time
import requests

is_logged_in = False


def on_login():
    global is_logged_in
    username = username_entry.get()
    password = password_entry.get()

    # Envio de dados para o servidor
    response = requests.post("https://tecnopriv.top/login-bot/login.php", data={
        "username": username,
        "password": password
    })

    if response.json().get('status') == 'success':
        messagebox.showinfo("Login", "Login bem-sucedido!")
        is_logged_in = True
        button_process['state'] = 'normal'  # Habilita o botão Processar Vídeo
    else:
        messagebox.showerror("Login", "Login e senha desativado, ultilize o programa")
        #Tire essa parte caso queira colocar login e senha
        is_logged_in = True
        button_process['state'] = 'normal'  # Habilita o botão Processar Vídeo




def download_video(url):
    yt = YouTube(url)
    video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    video.download(filename='video_baixado.mp4')
    return 'video_baixado.mp4'

def choose_video_source():
    choice = input("Digite '1' para inserir um link do YouTube ou '2' para escolher um arquivo local: ")
    if choice == '1':
        url = input("Insira o link do YouTube: ")
        return download_video(url)
    elif choice == '2':
        filepath = input("Insira o caminho completo do arquivo de vídeo: ")
        return filepath
    else:
        print("Escolha inválida.")
        return choose_video_source()

def resize_video(video_path, video_format, add_border=False):
    clip = VideoFileClip(video_path)
    if clip is None:
        print(f"Não foi possível carregar o vídeo resize de {video_path}")
        return

    w, h = clip.size

    if video_format == 'normal':
        return video_path  # Não redimensione o vídeo no formato normal
    elif video_format == '4:3':
        target_aspect_ratio = 4 / 3
    elif video_format == '3:4':
        target_aspect_ratio = 3 / 4
    elif video_format == 'tiktok':
        target_aspect_ratio = 9 / 16
        add_border = True

    x_center = w / 2
    y_center = h / 2

    if w / h > target_aspect_ratio:
        # Maior largura em relação à altura desejada; recorte horizontal
        new_width = int(h * target_aspect_ratio)
        x1 = max(x_center - new_width / 2, 0)
        y1 = 0
        new_height = h
    else:
        # Maior altura em relação à largura desejada; recorte vertical
        new_height = int(w / target_aspect_ratio)
        x1 = 0
        y1 = max(y_center - new_height / 2, 0)
        new_width = w

    cropped_clip = clip.crop(x1=x1, y1=y1, width=new_width, height=new_height)
    if add_border:
        cropped_clip = cropped_clip.margin(color=(0, 0, 0), left=10, right=10, top=10, bottom=10)
    
    resized_filename = f'video_editado_{video_format}.mp4'
    cropped_clip.write_videofile(resized_filename)
    return resized_filename





def change_video_speed(video_path, speed_factor=1.5):
    clip = VideoFileClip(video_path)
    if clip is None:
        print(f"Não foi possível carregar o vídeo speed de {video_path}")
        return
    
    # Alterando a velocidade do vídeo
    new_duration = clip.duration / speed_factor
    video = clip.fx(vfx.speedx, speed_factor).set_duration(new_duration)
    altered_speed_video_path = 'video_alterado_velocidade.mp4'
    video.write_videofile(altered_speed_video_path)
    return altered_speed_video_path
    

def remove_audio_from_video(video_path):
    video = VideoFileClip(video_path)
    video_without_audio = video.without_audio()
    output_path = os.path.splitext(video_path)[0] + '_sem_audio.mp4'
    video_without_audio.write_videofile(output_path)
    return output_path




def trim_video(video_path, start_time, end_time):
    if start_time == "00:00:00" and end_time == "00:00:00":
        return video_path  # Não faça corte no vídeo

    clip = VideoFileClip(video_path).subclip(start_time, end_time)
    if clip is None:
        print(f"Não foi possível carregar o vídeo trim de {video_path}")
        return
    trimmed_video_path = 'video_cortado.mp4'
    clip.write_videofile(trimmed_video_path)
    return trimmed_video_path

def change_audio_pitch(video_path, pitch_factor):
    video = VideoFileClip(video_path)
    # Carregar o áudio do vídeo e ajustar a duração
    audio = video.audio.set_duration(video.duration * pitch_factor)
    # Atribuir o novo áudio ao vídeo
    video_with_changed_pitch_path = 'video_alterado_audio.mp4'
    video.set_audio(audio).write_videofile(video_with_changed_pitch_path)
    return video_with_changed_pitch_path

def edit_video_ffmpeg(input_path, output_path, use_hevc=True, use_gpu=False, upscale_4k=False, preset_speed='medium'):
    if use_gpu:
        video_codec = 'h264_nvenc' if not use_hevc else 'hevc_nvenc'
    else:
        video_codec = 'libx264' if not use_hevc else 'libx265'

    ffmpeg_cmd = ['ffmpeg', '-i', input_path]

    if upscale_4k:
        # Adicionar filtros para escalar e ajustar o vídeo para 4K mantendo a proporção original
        ffmpeg_cmd += ['-vf', 'scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2']

    ffmpeg_cmd += [
        '-c:v', video_codec,
        '-preset', preset_speed,
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
        output_path
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    return output_path




def edit_video(video_path, use_hevc=True):
    # Primeiro, cria um vídeo temporário sem compressão
    temp_video_path = 'temp_uncompressed.mp4'
    clip = VideoFileClip(video_path)
    if clip is None:
        print(f"Não foi possível carregar o vídeo edit de {video_path}")
        return
    clip.write_videofile(temp_video_path, codec="libx264", audio_codec="aac", preset="ultrafast")

    # Define o caminho do vídeo editado
    edited_video_path = entry_output_filename.get() + '.mp4'

    # Agora usa o FFmpeg para aplicar os parâmetros do codec x265
    edit_video_ffmpeg(temp_video_path, edited_video_path, use_hevc)

    # Remove o vídeo temporário
    os.remove(temp_video_path)

    return edited_video_path


def add_metadata_with_ffmpeg(input_path, output_path, metadata):
    # Acessando o caminho do FFmpeg a partir da variável de ambiente
    ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')  # Use 'ffmpeg' como padrão se a variável de ambiente não estiver definida, baixe em "https://ffmpeg.org/download.html"
    # Comando para remover o HandlerDescription
    command = f'"{ffmpeg_path}" -i "{input_path}" -map_metadata -1 -metadata:s:v handler_name= -metadata:s:a handler_name='
    # Adiciona novos metadados
    metadata_flags = " ".join([f"-metadata {k}=\"{v}\"" for k, v in metadata.items()])
    command += f" {metadata_flags} -c copy \"{output_path}\""
    subprocess.run(command, shell=True, check=True)

    
# Funções da interface gráfica
def select_file():
    file_path = filedialog.askopenfilename()
    entry_video_path.delete(0, tk.END)
    entry_video_path.insert(0, file_path)

def download_from_youtube():
    url = simpledialog.askstring("Download do YouTube", "Insira o URL do YouTube:")
    if url:
        path = download_video(url)
        entry_video_path.delete(0, tk.END)
        entry_video_path.insert(0, path)
def choose_save_directory():
    directory = filedialog.askdirectory(initialdir=os.path.join(os.getenv('USERPROFILE'), 'Videos'))
    entry_save_path.delete(0, tk.END)
    entry_save_path.insert(0, directory)

def process_video():
    if not is_logged_in:
        messagebox.showerror("Erro", "Por favor, faça login primeiro.")
        return
    label_status.config(text="Vídeo em processamento...")
    video_path = entry_video_path.get()
    save_path = entry_save_path.get()
    output_filename = entry_output_filename.get() + '.mp4'
    output_filepath = os.path.join(save_path, output_filename)

    if not video_path:
        label_status.config(text="Por favor, selecione um vídeo primeiro.")
        return

    try:
        start_time = entry_start_time.get()
        end_time = entry_end_time.get()

        # Verificar se o vídeo precisa ser cortado
        if start_time != "00:00:00" or end_time != "00:00:00":
            trimmed_video_path = trim_video(video_path, start_time, end_time)
        else:
            trimmed_video_path = video_path

        # Verificar se o vídeo precisa ser redimensionado
        video_format = var_video_format.get()
        resized_video_path = resize_video(trimmed_video_path, video_format)

        # Ajustes nas variáveis de configuração
        use_hevc = var_codec.get() == "H.265"
        upscale_4k = var_4k_output.get() == 's.4k'
        use_gpu_for_processing = var_processing.get() == 'GPU'
        preset_speed = var_speed.get()
        edited_video_path = edit_video_ffmpeg(resized_video_path, output_filepath, use_hevc, use_gpu_for_processing, upscale_4k, preset_speed)


        # Coleta dos metadados do usuário
        latitude = entry_latitude.get()
        longitude = entry_longitude.get()
        try:
            latitude_value = float(latitude) if latitude else 0
            longitude_value = float(longitude) if longitude else 0
            location_iso6709 = f"{latitude_value:+}{longitude_value:+}/"
        except ValueError:
            location_iso6709 = "/"

        metadata = {
            'com.apple.quicktime.make': entry_make.get(),
            'com.apple.quicktime.model': entry_model.get(),
            'com.apple.quicktime.software': entry_software.get(),
            'com.apple.quicktime.location.ISO6709': location_iso6709,
            'com.apple.quicktime.author': entry_author.get(),
            'com.apple.quicktime.title': entry_title.get(),
            'com.apple.quicktime.description': entry_description.get(),
            'com.apple.quicktime.keywords': entry_keywords.get(),
            'com.apple.quicktime.comment': entry_comment.get(),
            'com.apple.quicktime.genre': entry_genre.get()
        }

        output_path_with_metadata = os.path.splitext(edited_video_path)[0] + '_com_metadados.mp4'
        add_metadata_with_ffmpeg(edited_video_path, output_path_with_metadata, metadata)

        # Verificar se o usuário escolheu remover o áudio
        final_output_path = output_path_with_metadata
        if var_audio_option.get() == 'without_audio':
            final_output_path = remove_audio_from_video(output_path_with_metadata)

        label_status.config(text=f"Vídeo processado com sucesso: {final_output_path}")
    except Exception as e:
        print(f"Erro ao processar o vídeo: {e}")
        print("Detalhes do Erro:", e.args)
        text_error_output.config(state='normal')
        text_error_output.delete(1.0, tk.END)
        text_error_output.insert(tk.END, f"Erro ao processar o vídeo: {e}\nDetalhes: {e.args}")
        text_error_output.config(state='disabled')
        label_status.config(text="Erro ao processar o vídeo.")

# Função para animar o texto "Tecno Priv" com efeito "Matrix"
def animate_text():
    for i in range(10):
        titulo_label.config(text="".join(["Tecno Priv"[j] if j != i else chr(65 + (i % 26)) for j in range(len("Tecno Priv"))]))
        root.update()
        time.sleep(0.2)
        # Agende a próxima execução da animação após 3 segundos
    root.after(3000, animate_text)
if __name__ == "__main__":
    
    # Interface gráfica
    root = Tk()    
    root.title("Editor Metadados e Vídeo - By Tecno Priv")

    var_processing = tk.StringVar(value='CPU')  # Valor padrão para processamento via CPU
    var_speed = tk.StringVar(value='medium')  # Variável para armazenar a velocidade de processamento

    # Layout principal
    main_frame = tk.Frame(root)
    main_frame.pack(padx=10, pady=10)
    

    # Dividindo o layout principal em duas colunas
    left_frame = tk.Frame(main_frame)
    left_frame.pack(side=tk.LEFT, padx=10, pady=10)

    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

    

    #LOGIN
    titulo_LOGIN = tk.Label(left_frame, text="FAÇA LOGIN", font=("Times New Roman", 25))
    titulo_LOGIN.pack()

    label_username = tk.Label(left_frame, text="Nome de usuário:")
    label_username.pack()

    username_entry = tk.Entry(left_frame)
    username_entry.insert(0, "admin")
    username_entry.pack()

    label_password = tk.Label(left_frame, text="Senha:")
    label_password.pack()

    password_entry = tk.Entry(left_frame, show="*")
    password_entry.insert(0, "admin")
    password_entry.pack()

    login_button = tk.Button(left_frame, text="Login", command=on_login)
    login_button.pack()

    # Crie o rótulo para "Tecno Priv - Efeito Matrix" com um tamanho de fonte maior
    titulo_label = tk.Label(left_frame, text="Tecno Priv", font=("Times New Roman", 25))
    titulo_label.pack()

    # Widgets da esquerda (exemplo)
    label_video_path = tk.Label(left_frame, text="Caminho do Vídeo:")
    label_video_path.pack()

    entry_video_path = tk.Entry(left_frame, width=50)
    entry_video_path.pack()

    button_browse = tk.Button(left_frame, text="Procurar Arquivo", command=select_file)
    button_browse.pack()

    button_download = tk.Button(left_frame, text="Baixar do YouTube", command=download_from_youtube)
    button_download.pack()

    # Adicionando um campo e botão para escolher o diretório de salvamento
    label_save_path = tk.Label(left_frame, text="Salvar em:")
    label_save_path.pack()
    entry_save_path = tk.Entry(left_frame, width=50)
    entry_save_path.insert(0, os.path.join(os.getenv('USERPROFILE'), 'Videos'))  # Caminho padrão da pasta de vídeos
    entry_save_path.pack()
    button_choose_directory = tk.Button(left_frame, text="Escolher Pasta", command=choose_save_directory)
    button_choose_directory.pack()

    # Adicionando um campo para o nome do arquivo de saída
    label_output_filename = tk.Label(left_frame, text="Nome do Arquivo de Saída:")
    label_output_filename.pack()
    entry_output_filename = tk.Entry(left_frame, width=50)
    entry_output_filename.insert(0, "MeuEditVideo")  # Valor padrão para o nome do arquivo
    entry_output_filename.pack()

    # Bordas separadoras
    separator1 = ttk.Separator(left_frame, orient='horizontal')
    separator1.pack(fill='x')

    # Campos para o tempo de corte
    label_start_time = tk.Label(left_frame, text="CASO NÃO QUEIRA CORTAR O VÍDEO, DEIXE NO PADRÃO 00:00:00")
    label_start_time.pack()
    label_start_time = tk.Label(left_frame, text="Tempo de início (hh:mm:ss), ex: '00:01:50':")
    label_start_time.pack()
    entry_start_time = tk.Entry(left_frame, width=20)
    entry_start_time.insert(0, "00:00:00")
    entry_start_time.pack()

    label_end_time = tk.Label(left_frame, text="Tempo de fim (hh:mm:ss), ex: '00:02:52':")
    label_end_time.pack()
    entry_end_time = tk.Entry(left_frame, width=20)
    entry_end_time.insert(0, "00:00:00")
    entry_end_time.pack()

    separator2 = ttk.Separator(left_frame, orient='horizontal')
    separator2.pack(fill='x')

    # Adicionando opção para escolher o formato do vídeo
    var_video_format = tk.StringVar(value='normal')
    radio_normal = tk.Radiobutton(left_frame, text="Formato Normal", variable=var_video_format, value='normal')
    radio_normal.pack()
    radio_tiktok = tk.Radiobutton(left_frame, text="Formato 4:3", variable=var_video_format, value='4:3')
    radio_tiktok.pack()
    radio_tiktok = tk.Radiobutton(left_frame, text="Formato 3:4", variable=var_video_format, value='3:4')
    radio_tiktok.pack()
    radio_tiktok = tk.Radiobutton(left_frame, text="Formato TikTok", variable=var_video_format, value='tiktok')
    radio_tiktok.pack()

    separator3 = ttk.Separator(left_frame, orient='horizontal')
    separator3.pack(fill='x')

    # Adicione os botões de rádio para escolha de processamento na sua interface
    speed_frame_left = tk.Frame(left_frame)
    speed_frame_left.pack()

    label_processing_choice = tk.Label(speed_frame_left, text="Escolha de Processamento:")
    label_processing_choice.pack()

    radio_cpu = tk.Radiobutton(speed_frame_left, text="Usar CPU", variable=var_processing, value='CPU')
    radio_cpu.pack(side=tk.LEFT)

    radio_gpu = tk.Radiobutton(speed_frame_left, text="Usar CPU + GPU", variable=var_processing, value='GPU')
    radio_gpu.pack(side=tk.LEFT)

     # Bordas separadoras
    separator1 = ttk.Separator(left_frame, orient='horizontal')
    separator1.pack(fill='x')

    # Definindo a variável para escolha de áudio
    var_audio_option = tk.StringVar(value='with_audio')

    # Adicionando os botões de rádio para escolha de áudio na interface gráfica
    label_audio_option = tk.Label(left_frame, text="Opções de Áudio:")
    label_audio_option.pack()

    radio_with_audio = tk.Radiobutton(left_frame, text="Manter Áudio", variable=var_audio_option, value='with_audio')
    radio_with_audio.pack()

    radio_without_audio = tk.Radiobutton(left_frame, text="Remover Áudio", variable=var_audio_option, value='without_audio')
    radio_without_audio.pack()

     # Bordas separadoras
    separator1 = ttk.Separator(left_frame, orient='horizontal')
    separator1.pack(fill='x')

    # Saida em 4k
    speed_frame_left = tk.Frame(left_frame)
    speed_frame_left.pack()

    label_4k_choice = tk.Label(speed_frame_left, text="Saída do Vídeo em 4k?")
    label_4k_choice.pack()
    var_4k_output = tk.StringVar(value='n.4k')
    radio_n4k = tk.Radiobutton(speed_frame_left, text="Não Usar 4k", variable=var_4k_output, value='n.4k')
    radio_n4k.pack(side=tk.LEFT)
    radio_s4k = tk.Radiobutton(speed_frame_left, text="Usar 4k", variable=var_4k_output, value='s.4k')
    radio_s4k.pack(side=tk.LEFT)
    

    # Bordas separadoras
    separator1 = ttk.Separator(left_frame, orient='horizontal')
    separator1.pack(fill='x')

    # Opções de codec
    label_codec_choice = tk.Label(left_frame, text="Escolha de Codec:")
    label_codec_choice.pack()
    var_codec = tk.StringVar(value='H.264')
    radio_h264 = tk.Radiobutton(left_frame, text="Usar codec H.264", variable=var_codec, value='H.264')
    radio_h264.pack()
    radio_h265 = tk.Radiobutton(left_frame, text="Usar codec H.265 (HEVC)", variable=var_codec, value='H.265')
    radio_h265.pack()

    # Campo para 'Make' com preenchimento padrão
    label_make = tk.Label(right_frame, text="Feito Por:")
    label_make.pack()
    entry_make = tk.Entry(right_frame, width=50)
    entry_make.insert(0, "Apple")
    entry_make.pack()

    # Campo para 'Model' com preenchimento padrão
    label_model = tk.Label(right_frame, text="Modelo:")
    label_model.pack()
    entry_model = tk.Entry(right_frame, width=50)
    entry_model.insert(0, "iPhone 13")
    entry_model.pack()

    # Campo para 'Software' com preenchimento padrão
    label_software = tk.Label(right_frame, text="Software:")
    label_software.pack()
    entry_software = tk.Entry(right_frame, width=50)
    entry_software.insert(0, "iOS 15.1")
    entry_software.pack()

    # Campo para 'Latitude' com preenchimento padrão
    label_latitude = tk.Label(right_frame, text="Latitude:")
    label_latitude.pack()
    entry_latitude = tk.Entry(right_frame, width=50)
    entry_latitude.insert(0, "-22.948612")
    entry_latitude.pack()

    # Campo para 'Longitude' com preenchimento padrão
    label_longitude = tk.Label(right_frame, text="Longitude:")
    label_longitude.pack()
    entry_longitude = tk.Entry(right_frame, width=50)
    entry_longitude.insert(0, "-43.156144")
    entry_longitude.pack()

    # Campo para 'Author' com preenchimento padrão
    label_author = tk.Label(right_frame, text="Autor:")
    label_author.pack()
    entry_author = tk.Entry(right_frame, width=50)
    entry_author.insert(0, "Fulano de Tal")
    entry_author.pack()

    # Campo para 'Title' com preenchimento padrão
    label_title = tk.Label(right_frame, text="Título:")
    label_title.pack()
    entry_title = tk.Entry(right_frame, width=50)
    entry_title.insert(0, "Férias Rio de Janeiro")
    entry_title.pack()

    # Campo para 'Description' com preenchimento padrão
    label_description = tk.Label(right_frame, text="Descrição:")
    label_description.pack()
    entry_description = tk.Entry(right_frame, width=50)
    entry_description.insert(0, "Descrição de Ferias.")
    entry_description.pack()

    # Campo para 'Keywords' com preenchimento padrão
    label_keywords = tk.Label(right_frame, text="Palavras Chave:")
    label_keywords.pack()
    entry_keywords = tk.Entry(right_frame, width=50)
    entry_keywords.insert(0, "ferias,rio-janeiro,brasil")
    entry_keywords.pack()

    # Campo para 'Comment' com preenchimento padrão
    label_comment = tk.Label(right_frame, text="Comentário:")
    label_comment.pack()
    entry_comment = tk.Entry(right_frame, width=50)
    entry_comment.insert(0, "Comentarios sobre ferias aqui.")
    entry_comment.pack()

    # Campo para 'Genre' com preenchimento padrão
    label_genre = tk.Label(right_frame, text="Genêro:")
    label_genre.pack()
    entry_genre = tk.Entry(right_frame, width=50)
    entry_genre.insert(0, "Viagem")
    entry_genre.pack()

    

    # Adicione os botões de rádio para a escolha de velocidade de processamento dentro do speed_frame
    # Frame para os botões de rádio da velocidade de processamento
    speed_frame_right = tk.Frame(right_frame)
    speed_frame_right.pack()

    label_speed_choice = tk.Label(speed_frame_right, text="Velocidade de Processamento(Influência na qualidade):")
    label_speed_choice.pack()

    radio_fast = tk.Radiobutton(speed_frame_right, text="Rápido", variable=var_speed, value='fast')
    radio_fast.pack(side=tk.LEFT)

    radio_medium = tk.Radiobutton(speed_frame_right, text="Médio", variable=var_speed, value='medium')
    radio_medium.pack(side=tk.LEFT)

    radio_slow = tk.Radiobutton(speed_frame_right, text="Devagar", variable=var_speed, value='slow')
    radio_slow.pack(side=tk.LEFT)

    radio_veryslow = tk.Radiobutton(speed_frame_right, text="Bem devagar", variable=var_speed, value='veryslow')
    radio_veryslow.pack(side=tk.LEFT)

    label_genre = tk.Label(right_frame, text="Faça Login para Processar Vídeo")
    label_genre.pack()
    button_process = tk.Button(right_frame, text="Processar Vídeo", command=process_video, state='disabled')
    button_process.pack()

    # Campo para exibir a saída de erro
    label_error_output = tk.Label(right_frame, text="Saída de Erro:")
    label_error_output.pack()
    text_error_output = scrolledtext.ScrolledText(right_frame, width=70, height=10, state='disabled')
    text_error_output.pack()

    label_status = tk.Label(right_frame, text="")
    label_status.pack()
    root.after(3000, animate_text)
    root.mainloop()

