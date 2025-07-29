from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User

from django.core.mail import send_mail
from django.conf import settings

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# import requests # <--- Jangan di-uncomment jika Anda tidak menggunakan fitur ERT API
from datetime import datetime # Diperlukan untuk timestamp pesan chat

from .models import Ticket, Comment, TicketActivity, Conversation, Message # <--- Tambahkan Conversation, Message
from .forms import TicketForm, CommentForm

class DashboardView(LoginRequiredMixin, View):
    template_name = 'tickets/dashboard.html'
    ACTIVITIES_PER_PAGE = 5 # <--- Definisikan berapa banyak aktivitas per halaman

    def get(self, request, *args, **kwargs):
        # Statistik Umum (untuk semua pengguna)
        total_tickets = Ticket.objects.all().count()
        open_tickets = Ticket.objects.filter(status='open').count()
        in_progress_tickets = Ticket.objects.filter(status='in_progress').count()
        resolved_tickets = Ticket.objects.filter(status='resolved').count()
        closed_tickets = Ticket.objects.filter(status='closed').count()

        context = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'closed_tickets': closed_tickets,
        }

        # Dapatkan nomor halaman untuk aktivitas dari GET request, default ke 1
        activity_page = request.GET.get('activity_page', 1)

        # Logika Aktivitas Terkini (dengan Pagination)
        if request.user.is_staff:
            # Staf melihat semua aktivitas
            all_activities = TicketActivity.objects.order_by('-timestamp')
            
            # Statistik untuk staf (tetap seperti sebelumnya, tidak terkait pagination aktivitas)
            my_assigned_tickets_open = Ticket.objects.filter(assigned_to=request.user, status__in=['open', 'in_progress', 'reopened']).count()
            my_assigned_tickets_resolved = Ticket.objects.filter(assigned_to=request.user, status__in=['resolved', 'closed']).count()

            raw_tickets_by_priority = Ticket.objects.values('priority').annotate(count=Count('priority')).order_by('-count')
            priority_display_map = dict(Ticket.PRIORITY_CHOICES)
            formatted_tickets_by_priority = []
            for item in raw_tickets_by_priority:
                display_priority = priority_display_map.get(item['priority'], item['priority'].replace('_', ' ').title())
                formatted_tickets_by_priority.append({
                    'display_name': display_priority,
                    'count': item['count']
                })
            raw_tickets_by_status = Ticket.objects.values('status').annotate(count=Count('status')).order_by('status')
            status_display_map = dict(Ticket.STATUS_CHOICES)
            formatted_tickets_by_status = []
            for item in raw_tickets_by_status:
                display_status = status_display_map.get(item['status'], item['status'].replace('_', ' ').title())
                formatted_tickets_by_status.append({
                    'display_name': display_status,
                    'count': item['count']
                })
            
            context.update({
                'my_assigned_tickets_open': my_assigned_tickets_open,
                'my_assigned_tickets_resolved': my_assigned_tickets_resolved,
                'tickets_by_priority': formatted_tickets_by_priority,
                'tickets_by_status': formatted_tickets_by_status,
            })
        else:
            # Pengguna biasa melihat aktivitas terkait tiket yang mereka buat
            all_activities = TicketActivity.objects.filter(ticket__created_by=request.user).order_by('-timestamp')
            
            # Statistik untuk pengguna biasa (tetap seperti sebelumnya)
            my_created_tickets_open = Ticket.objects.filter(created_by=request.user, status__in=['open', 'in_progress', 'reopened']).count()
            my_created_tickets_closed = Ticket.objects.filter(created_by=request.user, status__in=['resolved', 'closed']).count()
            
            context.update({
                'my_created_tickets_open': my_created_tickets_open,
                'my_created_tickets_closed': my_created_tickets_closed,
            })

        # --- Logika Pagination Aktivitas ---
        paginator = Paginator(all_activities, self.ACTIVITIES_PER_PAGE)
        try:
            activities_page_obj = paginator.page(activity_page)
        except PageNotAnInteger:
            activities_page_obj = paginator.page(1)
        except EmptyPage:
            activities_page_obj = paginator.page(paginator.num_pages)
        
        context['activities_page_obj'] = activities_page_obj # Masukkan page object ke context

        return render(request, self.template_name, context)

# --- Kelas dan Fungsi Lainnya (tetap sama) ---

class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        assigned_to_filter = self.request.GET.get('assigned_to')
        created_by_filter = self.request.GET.get('created_by')

        # Filter berdasarkan peran:
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(created_by__username__icontains=query) |
                Q(assigned_to__username__icontains=query)
            ).distinct()
        if status_filter:
            if status_filter == 'open_active': 
                queryset = queryset.filter(status__in=['open', 'in_progress', 'reopened'])
            elif status_filter == 'resolved_closed':
                queryset = queryset.filter(status__in=['resolved', 'closed'])
            else: 
                queryset = queryset.filter(status=status_filter)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        if assigned_to_filter and assigned_to_filter != 'all':
            if assigned_to_filter == 'unassigned':
                queryset = queryset.filter(assigned_to__isnull=True)
            elif assigned_to_filter == 'me':
                queryset = queryset.filter(assigned_to=self.request.user)
            else:
                try:
                    queryset = queryset.filter(assigned_to__pk=int(assigned_to_filter))
                except ValueError:
                    pass
        
        if created_by_filter == 'me':
            queryset = queryset.filter(created_by=self.request.user)
        elif created_by_filter and created_by_filter != 'all':
            try:
                queryset = queryset.filter(created_by__pk=int(created_by_filter))
            except ValueError:
                pass

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Ticket.STATUS_CHOICES
        context['priority_choices'] = Ticket.PRIORITY_CHOICES
        
        if self.request.user.is_staff:
            context['assignable_users'] = User.objects.filter(is_active=True, is_staff=True).order_by('username')
            context['all_users'] = User.objects.filter(is_active=True).order_by('username')
        else:
            context['assignable_users'] = []
            context['all_users'] = []
            
        context['current_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_assigned_to'] = self.request.GET.get('assigned_to', '')
        context['current_created_by'] = self.request.GET.get('created_by', '')
        return context

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'
    
    # ERT_API_URL = "http://127.0.0.1:8001/predict_ert" # Baris ini dikomentari di kode Anda

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['comment_form'] = CommentForm()
        context['activities'] = self.object.activities.all()

        if not self.request.user.is_staff and self.object.created_by != self.request.user:
            messages.error(self.request, 'Anda tidak memiliki izin untuk melihat tiket ini.')
            return redirect('ticket_list')

        # --- LOGIKA PANGGILAN API ERT (Tidak ada dalam kode yang Anda berikan) ---
        # Jika Anda ingin ERT, Anda perlu menambahkan kembali import requests dan logika panggilan API
        # seperti yang ada di balasan sebelumnya.
        # --- AKHIR LOGIKA PANGGILAN API ERT ---

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_staff and self.object.created_by != request.user:
            messages.error(request, 'Anda tidak memiliki izin untuk mengubah tiket ini.')
            return redirect('ticket_detail', pk=self.object.pk)

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = self.object
            comment.author = self.request.user
            comment.save()
            TicketActivity.objects.create(
                ticket=self.object,
                actor=self.request.user,
                action=f"Komentar baru ditambahkan: '{comment.content[:50]}{'...' if len(comment.content) > 50 else ''}'"
            )
            messages.success(request, 'Komentar berhasil ditambahkan!')
            return redirect('ticket_detail', pk=self.object.pk)
        else:
            context = self.get_context_data(object=self.object)
            context['comment_form'] = comment_form
            messages.error(request, 'Gagal menambahkan komentar. Harap periksa input Anda.')
            return self.render_to_response(context)

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('ticket_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        TicketActivity.objects.create(
            ticket=self.object,
            actor=self.request.user,
            action=f"Tiket dibuat dengan judul: '{self.object.title}'"
        )
        messages.success(self.request, 'Tiket berhasil dibuat!')

        # --- LOGIKA PENGIRIMAN EMAIL BARU ---
        admin_emails = [user.email for user in User.objects.filter(is_staff=True, is_active=True) if user.email]
        
        if admin_emails:
            subject = f'[SISTEM TIKET] Tiket Baru Dibuat: {self.object.title}'
            ticket_url = self.request.build_absolute_uri(self.object.get_absolute_url())
            
            message_body = (
                f'Halo,\n\n'
                f'Sebuah tiket baru telah dibuat oleh {self.request.user.username}:\n\n'
                f'Judul : {self.object.title}\n'
                f'Deskripsi : {self.object.description}\n'
                f'Prioritas : {self.object.get_priority_display()}\n\n'
                f'Untuk melihat detail tiket dan menanganinya, kunjungi:\n'
                f'{ticket_url}\n\n'
                f'Terima kasih,\nTim IT Support'
            )
            
            from_email = '"Ticketing"'
            recipient_list = admin_emails

            try:
                send_mail(
                    subject,
                    message_body,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )
                messages.info(self.request, 'Notifikasi telah terkirim kepada Tim IT.')
            except Exception as e:
                messages.error(self.request, f'Gagal mengirim notifikasi email: {e}')
        # --- AKHIR LOGIKA PENGIRIMAN EMAIL BARU ---

        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Gagal membuat tiket. Harap periksa input Anda.')
        return super().form_invalid(form)

class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_form.html'
    context_object_name = 'ticket'

    def get_success_url(self):
        messages.success(self.request, 'Tiket berhasil diperbarui!')
        return reverse_lazy('ticket_detail', kwargs={'pk': self.object.pk})

    def test_func(self):
        ticket = self.get_object()
        return self.request.user.is_staff or \
               self.request.user == ticket.created_by

    def form_valid(self, form):
        original_ticket = Ticket.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        updated_ticket = self.object

        changes = []
        if original_ticket.title != updated_ticket.title:
            changes.append(f"Judul diubah dari '{original_ticket.title}' menjadi '{updated_ticket.title}'")
        if original_ticket.description != updated_ticket.description:
            if len(original_ticket.description) != len(updated_ticket.description) or \
               original_ticket.description[:50] != updated_ticket.description[:50]:
                changes.append(f"Deskripsi diubah.")
        
        if original_ticket.status != updated_ticket.status:
            changes.append(f"Status diubah dari '{original_ticket.get_status_display()}' menjadi '{updated_ticket.get_status_display()}'")
        
        if original_ticket.priority != updated_ticket.priority:
            changes.append(f"Prioritas diubah dari '{original_ticket.get_priority_display()}' menjadi '{updated_ticket.get_priority_display()}'")
        
        original_assigned_to_name = original_ticket.assigned_to.username if original_ticket.assigned_to else 'None'
        updated_assigned_to_name = updated_ticket.assigned_to.username if updated_ticket.assigned_to else 'None'
        if original_assigned_to_name != updated_assigned_to_name:
            changes.append(f"Ditugaskan kepada diubah dari '{original_assigned_to_name}' menjadi '{updated_assigned_to_name}'")

        if changes:
            action_text = "Tiket diperbarui: " + ", ".join(changes)
            TicketActivity.objects.create(
                ticket=self.object,
                actor=self.request.user,
                action=action_text
            )
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Gagal memperbarui tiket. Harap periksa input Anda.')
        return super().form_invalid(form)

    def handle_no_permission(self):
        messages.error(self.request, 'Anda tidak memiliki izin untuk mengedit tiket ini.')
        return redirect('ticket_detail', pk=self.get_object().pk)

class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket
    template_name = 'tickets/ticket_confirm_delete.html'
    success_url = reverse_lazy('ticket_list')
    context_object_name = 'ticket'

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        ticket_to_delete = self.get_object()
        TicketActivity.objects.create(
            ticket=ticket_to_delete,
            actor=request.user,
            action=f"Tiket dihapus: '{ticket_to_delete.title}'"
        )
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Tiket berhasil dihapus!')
        return response

    def handle_no_permission(self):
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus tiket ini.')
        return redirect('ticket_detail', pk=self.get_object().pk)


@login_required
def assign_ticket_to_me(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak memiliki izin untuk menugaskan tiket.')
        return redirect('ticket_detail', pk=pk)

    if ticket.assigned_to != request.user:
        old_assignee_name = ticket.assigned_to.username if ticket.assigned_to else 'None'
        ticket.assigned_to = request.user
        status_change_text = ""
        if ticket.status == 'open':
            ticket.status = 'in_progress'
            status_change_text = "dan status diubah menjadi 'In Progress'"
        ticket.save()
        TicketActivity.objects.create(
            ticket=ticket,
            actor=request.user,
            action=f"Tiket ditugaskan dari '{old_assignee_name}' ke '{request.user.username}' {status_change_text}."
        )
        messages.success(request, f"Tiket '{ticket.title}' berhasil ditugaskan kepada Anda {status_change_text}.")
    else:
        messages.info(request, "Tiket ini sudah ditugaskan kepada Anda.")
    return redirect('ticket_detail', pk=pk)
