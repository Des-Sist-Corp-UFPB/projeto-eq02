package br.ufpb.dsc.cirurgias.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDateTime;

@Entity
@Table(name = "cirurgia")
public class Cirurgia {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne @JoinColumn(name = "paciente_id")
    private Paciente paciente;
    
    @ManyToOne @JoinColumn(name = "medico_id")
    private Medico medico;
    
    @ManyToOne @JoinColumn(name = "hospital_id")
    private Hospital hospital;
    
    @ManyToOne @JoinColumn(name = "tipo_cirurgia_id")
    private TipoCirurgia tipoCirurgia;
    
    @Column(name = "data_hora")
    private LocalDateTime dataHora;
    
    @Enumerated(EnumType.STRING)
    private StatusCirurgia status;
    
    @Column(name = "criado_em", nullable = false, updatable = false)
    private Instant criadoEm;
    @Column(name = "atualizado_em", nullable = false)
    private Instant atualizadoEm;

    @PrePersist protected void prePersist() { criadoEm = atualizadoEm = Instant.now(); }
    @PreUpdate protected void preUpdate() { atualizadoEm = Instant.now(); }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Paciente getPaciente() { return paciente; }
    public void setPaciente(Paciente paciente) { this.paciente = paciente; }
    public Medico getMedico() { return medico; }
    public void setMedico(Medico medico) { this.medico = medico; }
    public Hospital getHospital() { return hospital; }
    public void setHospital(Hospital hospital) { this.hospital = hospital; }
    public TipoCirurgia getTipoCirurgia() { return tipoCirurgia; }
    public void setTipoCirurgia(TipoCirurgia tipoCirurgia) { this.tipoCirurgia = tipoCirurgia; }
    public LocalDateTime getDataHora() { return dataHora; }
    public void setDataHora(LocalDateTime dataHora) { this.dataHora = dataHora; }
    public StatusCirurgia getStatus() { return status; }
    public void setStatus(StatusCirurgia status) { this.status = status; }
}
