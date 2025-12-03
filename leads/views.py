import csv
import json
from typing import Any, Dict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView, ListView, TemplateView, UpdateView

from .forms import (
    LeadUpdateForm,
    ProfileForm,
    PublicLeadForm,
    SignupForm,
)
from .models import BusinessProfile, Lead


class HomeView(TemplateView):
    """Simple marketing-style landing page."""

    template_name = 'home.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any):
        if request.user.is_authenticated:
            return redirect('leads:dashboard')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, ListView):
    template_name = 'leads/dashboard.html'
    context_object_name = 'leads'
    paginate_by = 10

    def get_queryset(self):
        queryset = Lead.objects.filter(owner=self.request.user)
        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip().upper()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search)
            )
        if status in dict(Lead.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.business_profile
        context['profile'] = profile
        context['embed_script_url'] = self.request.build_absolute_uri(
            profile.embed_script_url()
        )
        object_list = getattr(self, 'object_list', None)
        if hasattr(object_list, 'count'):
            context['total_leads'] = object_list.count()
        elif object_list is not None:
            context['total_leads'] = len(object_list)
        else:
            context['total_leads'] = 0
        context['query'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Lead.STATUS_CHOICES
        return context


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadUpdateForm
    template_name = 'leads/lead_form.html'

    def get_queryset(self):
        return Lead.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Lead updated.')
        return super().form_valid(form)


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    model = Lead
    success_url = reverse_lazy('leads:dashboard')
    template_name = 'leads/lead_confirm_delete.html'

    def get_queryset(self):
        return Lead.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.info(self.request, 'Lead deleted.')
        return super().delete(request, *args, **kwargs)


class CSVExportView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        leads = Lead.objects.filter(owner=request.user).order_by('created_at')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="leads_export.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            ['Name', 'Email', 'Phone', 'Message', 'Status', 'Notes', 'Created At']
        )
        for lead in leads:
            writer.writerow(
                [
                    lead.name,
                    lead.email,
                    lead.phone,
                    lead.message,
                    lead.get_status_display(),
                    lead.notes,
                    lead.created_at.isoformat(),
                ]
            )
        return response


class PublicLeadCaptureView(View):
    template_name = 'leads/public_form.html'

    def get_profile(self, public_id: str) -> BusinessProfile:
        return get_object_or_404(BusinessProfile, public_id=public_id)

    def get(self, request, public_id):
        profile = self.get_profile(public_id)
        form = PublicLeadForm()
        embed_mode = request.GET.get('embed') == '1'
        return render(
            request,
            self.template_name,
            {
                'form': form,
                'profile': profile,
                'submitted': False,
                'embed_mode': embed_mode,
                'hide_nav': embed_mode,
                'compact_layout': embed_mode,
            },
        )

    def post(self, request, public_id):
        profile = self.get_profile(public_id)
        form = PublicLeadForm(request.POST)
        embed_mode = request.GET.get('embed') == '1'
        if form.is_valid():
            lead = form.save(commit=False)
            lead.owner = profile.user
            lead.save()
            self._send_notification(profile, lead)
            return render(
                request,
                self.template_name,
                {
                    'form': PublicLeadForm(),
                    'profile': profile,
                    'submitted': True,
                    'embed_mode': embed_mode,
                    'hide_nav': embed_mode,
                    'compact_layout': embed_mode,
                },
                status=201,
            )
        return render(
            request,
            self.template_name,
                {
                    'form': form,
                    'profile': profile,
                    'submitted': False,
                    'embed_mode': embed_mode,
                    'hide_nav': embed_mode,
                    'compact_layout': embed_mode,
                },
                status=400,
            )

    def _send_notification(self, profile: BusinessProfile, lead: Lead) -> None:
        to_email = profile.notification_email or profile.user.email
        if not to_email:
            return
        subject = f'Lead baru dari {profile.business_name}'
        body = (
            f'Lead baru diterima.\n'
            f'Nama: {lead.name}\n'
            f'Email: {lead.email}\n'
            f'Phone: {lead.phone}\n'
            f'Pesan: {lead.message}\n'
        )
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=True,
        )


class EmbedScriptView(View):
    """Return a JS snippet that renders an iframe-based embed."""

    def get(self, request: HttpRequest, public_id: str) -> HttpResponse:
        profile = get_object_or_404(BusinessProfile, public_id=public_id)
        form_url = (
            request.build_absolute_uri(
                reverse('leads:public_form', args=[profile.public_id])
            )
            + '?embed=1'
        )
        script = (
            "(function(){"
            "var container=document.currentScript.parentElement;"
            "var iframe=document.createElement('iframe');"
            f"iframe.src={json.dumps(form_url)};"
            "iframe.loading='lazy';"
            "iframe.style.width='100%';"
            "iframe.style.border='0';"
            "iframe.style.minHeight='430px';"
            "container.appendChild(iframe);"
            "})();"
        )
        return HttpResponse(script, content_type='application/javascript')


class SignupView(View):
    template_name = 'registration/signup.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('leads:dashboard')
        return render(request, self.template_name, {'form': SignupForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('leads:dashboard')
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Akun berhasil dibuat.')
            return redirect('leads:dashboard')
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'leads/profile.html'

    def get(self, request):
        profile = request.user.business_profile
        return render(
            request,
            self.template_name,
            {'form': ProfileForm(instance=profile), 'profile': profile},
        )

    def post(self, request):
        profile = request.user.business_profile
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil bisnis diperbarui.')
            return redirect('leads:profile')
        return render(
            request, self.template_name, {'form': form, 'profile': profile}
        )
